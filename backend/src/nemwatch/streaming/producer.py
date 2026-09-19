import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from nemwatch.config import Settings
from nemwatch.domain.events import AlertRaisedV1, DispatchObservedV1
from nemwatch.domain.models import Alert, DispatchRecord


def serialize_event(event: BaseModel) -> bytes:
    return json.dumps(
        event.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class EventProducer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            acks="all",
            request_timeout_ms=settings.kafka_request_timeout_ms,
            max_request_size=settings.kafka_max_event_bytes,
            client_id="nemwatch-producer",
        )

    async def start(self) -> None:
        await self._producer.start()

    async def stop(self) -> None:
        await self._producer.flush()
        await self._producer.stop()

    async def publish_dispatch(self, record: DispatchRecord, correlation_id: UUID) -> None:
        event = DispatchObservedV1(correlation_id=correlation_id, payload=record)
        key = f"{record.region.value}|{record.interval_datetime.isoformat()}".encode()
        await self._producer.send_and_wait(
            self.settings.dispatch_topic, serialize_event(event), key=key
        )

    async def publish_alert(self, alert: Alert, correlation_id: UUID) -> None:
        event = AlertRaisedV1(correlation_id=correlation_id, payload=alert)
        key = f"{alert.rule_key}|{alert.region.value}|{alert.interval_datetime.isoformat()}".encode()
        await self._producer.send_and_wait(
            self.settings.alert_topic, serialize_event(event), key=key
        )

    async def publish_dead_letter(
        self, *, source_topic: str, partition: int, offset: int, reason: str
    ) -> None:
        body: dict[str, Any] = {
            "event_type": "nem.event.rejected.v1",
            "occurred_at": datetime.now(UTC).isoformat(),
            "source_topic": source_topic,
            "partition": partition,
            "offset": offset,
            "reason": reason[:160],
        }
        await self._producer.send_and_wait(
            self.settings.dead_letter_topic,
            json.dumps(body, sort_keys=True, separators=(",", ":")).encode(),
            key=f"{source_topic}|{partition}|{offset}".encode(),
        )
