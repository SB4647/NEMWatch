from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from nemwatch.api.dependencies import get_dispatch_repository
from nemwatch.api.main import create_app
from nemwatch.config import Settings
from nemwatch.domain.models import DispatchRecord, Region


class FakeDispatchRepository:
    async def get_latest(self, region: Region):
        return DispatchRecord(
            region=region, interval_datetime=datetime(2026, 1, 1, tzinfo=UTC),
            price=Decimal("100.25"), demand=Decimal("7000"), source_file="fixture.csv", source_row=2,
        )

    async def get_history(self, region, start, end, limit, offset):
        return [await self.get_latest(region)]


def client() -> TestClient:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    app.dependency_overrides[get_dispatch_repository] = lambda: FakeDispatchRepository()
    return TestClient(app)


def test_latest_serializes_decimals_as_strings() -> None:
    response = client().get("/api/v1/dispatch/latest?region=QLD1")
    assert response.status_code == 200
    assert response.json()[0]["price"] == "100.25"


def test_history_rejects_reversed_range() -> None:
    response = client().get(
        "/api/v1/dispatch/history",
        params={"region": "QLD1", "start": "2026-01-02T00:00:00Z", "end": "2026-01-01T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_range"


def test_history_rejects_excessive_range() -> None:
    response = client().get(
        "/api/v1/dispatch/history",
        params={"region": "QLD1", "start": "2026-01-01T00:00:00Z", "end": "2026-02-02T00:00:00Z"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "range_too_large"
