from aiokafka import AIOKafkaConsumer

from nemwatch.config import Settings


def create_dispatch_consumer(settings: Settings) -> AIOKafkaConsumer:
    return AIOKafkaConsumer(
        settings.dispatch_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.processor_consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
        request_timeout_ms=settings.kafka_request_timeout_ms,
        max_partition_fetch_bytes=settings.kafka_max_event_bytes,
        client_id="nemwatch-processor",
    )
