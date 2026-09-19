from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import UUID, uuid4
from time import perf_counter

from nemwatch.domain.models import DispatchRecord, RejectedRow
from nemwatch.ingestion.parser import parse_dispatch_csv
from nemwatch.observability.metrics import INGESTION_DURATION, INGESTION_ROWS

PublishDispatch = Callable[[DispatchRecord, UUID], Awaitable[None]]


@dataclass(frozen=True)
class IngestionResult:
    valid: int
    rejected: int
    published: int
    rejected_rows: tuple[RejectedRow, ...]


class IngestionService:
    def __init__(self, publish: PublishDispatch) -> None:
        self.publish = publish

    async def ingest_csv(self, content: str, source: str) -> IngestionResult:
        started = perf_counter()
        try:
            parsed = parse_dispatch_csv(content, source)
            correlation_id = uuid4()
            published = 0
            for record in parsed.records:
                await self.publish(record, correlation_id)
                published += 1
            INGESTION_ROWS.labels("valid").inc(len(parsed.records))
            INGESTION_ROWS.labels("rejected").inc(len(parsed.rejected))
            INGESTION_ROWS.labels("published").inc(published)
            return IngestionResult(
                valid=len(parsed.records), rejected=len(parsed.rejected), published=published,
                rejected_rows=parsed.rejected,
            )
        finally:
            INGESTION_DURATION.observe(perf_counter() - started)
