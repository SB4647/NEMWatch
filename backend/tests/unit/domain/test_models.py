from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from nemwatch.domain.models import Alert, AlertRuleType, DispatchRecord, Region, Severity


def test_dispatch_record_normalizes_timestamp_to_utc() -> None:
    record = DispatchRecord(
        region=Region.QLD1,
        interval_datetime=datetime(2026, 1, 1, tzinfo=UTC),
        price=Decimal("123.45"), demand=Decimal("7000"),
        source_file="fixture.csv", source_row=2,
    )
    assert record.interval_datetime.tzinfo is UTC


def test_dispatch_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        DispatchRecord(
            region=Region.QLD1, interval_datetime=datetime(2026, 1, 1),
            price=Decimal("1"), demand=Decimal("1"), source_file="fixture.csv", source_row=2,
        )


def test_alert_trims_acknowledgement_note() -> None:
    alert = Alert(
        idempotency_key="high-price|QLD1|2026-01-01", rule_key="high-price",
        rule_type=AlertRuleType.HIGH_PRICE, region=Region.QLD1,
        interval_datetime=datetime(2026, 1, 1, tzinfo=UTC), severity=Severity.WARNING,
        message="High price", observed_value=Decimal("500"), threshold=Decimal("300"),
        acknowledgement_note="  reviewed  ",
    )
    assert alert.acknowledgement_note == "reviewed"
