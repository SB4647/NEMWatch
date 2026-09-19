from fastapi.testclient import TestClient

from nemwatch.api.main import create_app
from nemwatch.config import Settings


def test_liveness_does_not_require_dependencies() -> None:
    app = create_app(Settings(
        database_url="postgresql://user:pass@unreachable:5432/nemwatch",
        kafka_bootstrap_servers="unreachable:9092",
    ))
    response = TestClient(app).get("/health/live")
    assert response.status_code == 200


def test_metrics_endpoint_uses_prometheus_content_type() -> None:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    response = TestClient(app).get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "nemwatch_http_requests_total" in response.text
