from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

from nemwatch.config import Settings


async def ensure_topics(settings: Settings) -> None:
    admin = AIOKafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        request_timeout_ms=settings.kafka_request_timeout_ms,
        client_id="nemwatch-topic-admin",
    )
    await admin.start()
    try:
        topics = [
            NewTopic(name=settings.dispatch_topic, num_partitions=5, replication_factor=1),
            NewTopic(name=settings.alert_topic, num_partitions=5, replication_factor=1),
            NewTopic(name=settings.dead_letter_topic, num_partitions=1, replication_factor=1),
        ]
        existing = await admin.list_topics()
        missing = [topic for topic in topics if topic.name not in existing]
        if missing:
            try:
                await admin.create_topics(missing)
            except TopicAlreadyExistsError:
                pass
    finally:
        await admin.close()
