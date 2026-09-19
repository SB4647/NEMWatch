import asyncio
from collections.abc import Callable
from datetime import UTC, datetime

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import OffsetAndMetadata, TopicPartition
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nemwatch.domain.events import DispatchObservedV1
from nemwatch.domain.models import Alert, AlertRule, AlertRuleType, DispatchRecord, Region
from nemwatch.persistence.repositories import AlertRepository, DispatchRepository
from nemwatch.observability.metrics import ALERTS, EVENTS
from nemwatch.streaming.producer import EventProducer

AlertEvaluator = Callable[
    [DispatchRecord, DispatchRecord | None, datetime, list[AlertRule]], tuple[Alert, ...]
]


def no_alerts(
    _current: DispatchRecord,
    _previous: DispatchRecord | None,
    _now: datetime,
    _rules: list[AlertRule],
) -> tuple[Alert, ...]:
    return ()


class ProcessorService:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        producer: EventProducer,
        session_factory: async_sessionmaker[AsyncSession],
        evaluate: AlertEvaluator = no_alerts,
        stale_interval_seconds: float = 60.0,
    ) -> None:
        self.consumer = consumer
        self.producer = producer
        self.session_factory = session_factory
        self.evaluate = evaluate
        self.stale_interval_seconds = stale_interval_seconds

    async def run(self, stop_event: asyncio.Event) -> None:
        await self.consumer.start()
        await self.producer.start()
        stale_task = asyncio.create_task(self._stale_loop(stop_event))
        try:
            async for message in self.consumer:
                if stop_event.is_set():
                    break
                await self.process_message(message)
        finally:
            stale_task.cancel()
            await self.consumer.stop()
            await self.producer.stop()

    async def process_message(self, message: object) -> None:
        topic = str(message.topic)  # type: ignore[attr-defined]
        partition = int(message.partition)  # type: ignore[attr-defined]
        offset = int(message.offset)  # type: ignore[attr-defined]
        try:
            event = DispatchObservedV1.model_validate_json(message.value)  # type: ignore[attr-defined]
        except (ValidationError, ValueError, TypeError):
            await self.producer.publish_dead_letter(
                source_topic=topic, partition=partition, offset=offset,
                reason="dispatch_event_validation_failed",
            )
            await self._commit(topic, partition, offset)
            EVENTS.labels("consume", topic, "dead_letter").inc()
            return

        new_alerts: list[Alert] = []
        async with self.session_factory() as session:
            dispatches = DispatchRepository(session)
            alert_repository = AlertRepository(session)
            async with session.begin():
                previous = await dispatches.get_previous(
                    event.payload.region, event.payload.interval_datetime
                )
                await dispatches.upsert(event.payload)
                rules = await alert_repository.enabled_rules()
                alerts = self.evaluate(event.payload, previous, datetime.now(UTC), rules)
                for alert in alerts:
                    if await alert_repository.insert_if_absent(alert):
                        new_alerts.append(alert)
        for alert in new_alerts:
            await self.producer.publish_alert(alert, event.correlation_id)
            ALERTS.labels(alert.rule_key, alert.region.value).inc()
        EVENTS.labels("process", topic, "success").inc()
        await self._commit(topic, partition, offset)

    async def _stale_loop(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.stale_interval_seconds)
                continue
            except TimeoutError:
                pass
            now = datetime.now(UTC)
            for region in Region:
                new_alerts: list[Alert] = []
                async with self.session_factory() as session:
                    dispatches = DispatchRepository(session)
                    alert_repository = AlertRepository(session)
                    async with session.begin():
                        latest = await dispatches.get_latest(region)
                        if latest is None:
                            continue
                        rules = [
                            rule for rule in await alert_repository.enabled_rules()
                            if rule.rule_type is AlertRuleType.STALE_DATA
                        ]
                        for alert in self.evaluate(latest, None, now, rules):
                            if await alert_repository.insert_if_absent(alert):
                                new_alerts.append(alert)
                for alert in new_alerts:
                    await self.producer.publish_alert(alert, alert.id)
                    ALERTS.labels(alert.rule_key, alert.region.value).inc()

    async def _commit(self, topic: str, partition: int, offset: int) -> None:
        await self.consumer.commit({
            TopicPartition(topic, partition): OffsetAndMetadata(offset + 1, "")
        })
