import asyncio
import json
from contextlib import suppress

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from nemwatch.api.schemas import AlertResponse, DispatchResponse
from nemwatch.config import Settings
from nemwatch.domain.events import AlertRaisedV1, DispatchObservedV1
from nemwatch.live.hub import ConnectionHub


async def consume_market_events(settings: Settings, hub: ConnectionHub, stop: asyncio.Event) -> None:
    consumer = AIOKafkaConsumer(
        settings.dispatch_topic, settings.alert_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.live_consumer_group, auto_offset_reset="latest",
        enable_auto_commit=True, request_timeout_ms=settings.kafka_request_timeout_ms,
    )
    await consumer.start()
    try:
        async for message in consumer:
            if stop.is_set():
                return
            try:
                if message.topic == settings.dispatch_topic:
                    event = DispatchObservedV1.model_validate_json(message.value)
                    body = {"type": "dispatch_observed", "data": DispatchResponse.from_domain(event.payload).model_dump(mode="json")}
                else:
                    event = AlertRaisedV1.model_validate_json(message.value)
                    body = {"type": "alert_raised", "data": AlertResponse.from_domain(event.payload).model_dump(mode="json")}
                await hub.broadcast(body)
            except (ValidationError, ValueError, json.JSONDecodeError):
                continue
    finally:
        with suppress(Exception):
            await consumer.stop()
