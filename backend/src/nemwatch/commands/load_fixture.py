import asyncio
import json
from pathlib import Path
from uuid import UUID

from nemwatch.domain.models import DispatchRecord
from nemwatch.ingestion.service import IngestionService

FIXTURE = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "dispatch_sample.csv"


async def _count_publish(_record: DispatchRecord, _correlation_id: UUID) -> None:
    return None


async def main() -> None:
    result = await IngestionService(_count_publish).ingest_csv(FIXTURE.read_text(encoding="utf-8"), FIXTURE.name)
    print(json.dumps({"source": FIXTURE.name, "valid": result.valid, "rejected": result.rejected, "published": result.published}, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
