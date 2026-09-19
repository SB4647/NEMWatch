from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import UUID, uuid4

from nemwatch.domain.models import DispatchRecord, RejectedRow
from nemwatch.ingestion.parser import parse_dispatch_csv

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
        parsed = parse_dispatch_csv(content, source)
        correlation_id = uuid4()
        published = 0
        for record in parsed.records:
            await self.publish(record, correlation_id)
            published += 1
        return IngestionResult(
            valid=len(parsed.records), rejected=len(parsed.rejected), published=published,
            rejected_rows=parsed.rejected,
        )
