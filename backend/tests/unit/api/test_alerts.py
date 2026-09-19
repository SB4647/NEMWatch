from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from nemwatch.api.dependencies import get_alert_repository
from nemwatch.api.main import create_app
from nemwatch.config import Settings
from nemwatch.domain.models import Alert, AlertRuleType, Region, Severity


class FakeSession:
    async def commit(self) -> None:
        return None


class FakeAlertRepository:
    session = FakeSession()

    async def list(self, **_filters):
        return []

    async def acknowledge(self, alert_id, note, acknowledged_at):
        if str(alert_id).endswith("0000"):
            return None
        return Alert(
            id=alert_id, idempotency_key="high|QLD1|one", rule_key="high",
            rule_type=AlertRuleType.HIGH_PRICE, region=Region.QLD1,
            interval_datetime=datetime(2026, 1, 1, tzinfo=UTC), severity=Severity.WARNING,
            message="High price", observed_value=Decimal("500"), threshold=Decimal("300"),
            acknowledged_at=acknowledged_at, acknowledgement_note=note,
        )


def client() -> TestClient:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    app.dependency_overrides[get_alert_repository] = lambda: FakeAlertRepository()
    return TestClient(app)


def test_alerts_empty_page_is_stable() -> None:
    response = client().get("/api/v1/alerts")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_acknowledgement_returns_trimmed_note() -> None:
    response = client().post(f"/api/v1/alerts/{uuid4()}/acknowledge", json={"note": " reviewed "})
    assert response.status_code == 200
    assert response.json()["acknowledgement_note"] == "reviewed"
