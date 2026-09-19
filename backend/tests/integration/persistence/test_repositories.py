from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from nemwatch.domain.models import DispatchRecord, Region
from nemwatch.persistence.repositories import DispatchRepository
from nemwatch.persistence.tables import DispatchObservationRow


@pytest.mark.integration
async def test_duplicate_region_interval_updates_one_row(db_session) -> None:
    repository = DispatchRepository(db_session)
    first = DispatchRecord(
        region=Region.QLD1, interval_datetime=datetime(2026, 1, 1, tzinfo=UTC),
        price=Decimal("100"), demand=Decimal("7000"), source_file="one.csv", source_row=2,
    )
    second = first.model_copy(update={"price": Decimal("125"), "source_file": "two.csv"})
    await repository.upsert(first)
    await repository.upsert(second)
    await db_session.commit()
    assert await db_session.scalar(select(func.count()).select_from(DispatchObservationRow)) == 1
    assert (await repository.get_latest(Region.QLD1)).price == Decimal("125")
