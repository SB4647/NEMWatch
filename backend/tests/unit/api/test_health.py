from fastapi.testclient import TestClient

from nemwatch.api.main import create_app
from nemwatch.config import Settings


def test_liveness_contract() -> None:
    settings = Settings(
        database_url="postgresql://user:pass@unreachable:5432/nemwatch",
        kafka_bootstrap_servers="unreachable:9092",
    )

    response = TestClient(create_app(settings)).get("/health/live")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "service": "nemwatch-api"}
