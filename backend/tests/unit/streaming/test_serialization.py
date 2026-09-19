import json
from datetime import UTC, datetime
from decimal import Decimal

from nemwatch.domain.events import DispatchObservedV1
from nemwatch.domain.models import DispatchRecord, Region
from nemwatch.streaming.producer import serialize_event


def test_dispatch_event_round_trips_with_decimal_strings() -> None:
    event = DispatchObservedV1(payload=DispatchRecord(
        region=Region.QLD1, interval_datetime=datetime(2026, 1, 1, tzinfo=UTC),
        price=Decimal("94.50"), demand=Decimal("7150.00"),
        source_file="fixture.csv", source_row=2,
    ))
    encoded = serialize_event(event)
    assert json.loads(encoded)["payload"]["price"] == "94.50"
    assert DispatchObservedV1.model_validate_json(encoded).payload == event.payload
