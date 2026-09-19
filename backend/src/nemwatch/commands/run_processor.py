import asyncio
import signal

from prometheus_client import start_http_server

from nemwatch.config import Settings
from nemwatch.alerts.rules import evaluate_alerts
from nemwatch.persistence.database import create_engine, create_session_factory
from nemwatch.processing.service import ProcessorService
from nemwatch.streaming.consumer import create_dispatch_consumer
from nemwatch.streaming.producer import EventProducer
from nemwatch.streaming.topics import ensure_topics
from nemwatch.observability.logging import configure_logging


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    configure_logging("nemwatch-processor", settings.log_level)
    start_http_server(settings.processor_metrics_port, addr="0.0.0.0")
    await ensure_topics(settings)
    engine = create_engine(settings)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(name, stop_event.set)
    service = ProcessorService(
        create_dispatch_consumer(settings), EventProducer(settings), create_session_factory(engine),
        evaluate_alerts, settings.stale_check_interval_seconds,
    )
    try:
        await service.run(stop_event)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
