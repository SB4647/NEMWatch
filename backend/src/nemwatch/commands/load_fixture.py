import asyncio
import json
from pathlib import Path
from nemwatch.config import Settings
from nemwatch.ingestion.service import IngestionService
from nemwatch.streaming.producer import EventProducer
from nemwatch.streaming.topics import ensure_topics

FIXTURE = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "dispatch_sample.csv"


async def main() -> None:
    settings = Settings()  # type: ignore[call-arg]
    await ensure_topics(settings)
    producer = EventProducer(settings)
    await producer.start()
    try:
        result = await IngestionService(producer.publish_dispatch).ingest_csv(
            FIXTURE.read_text(encoding="utf-8"), FIXTURE.name
        )
    finally:
        await producer.stop()
    print(json.dumps({
        "source": FIXTURE.name, "valid": result.valid,
        "rejected": result.rejected, "published": result.published,
    }, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
