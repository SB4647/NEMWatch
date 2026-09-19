from fastapi.testclient import TestClient

from nemwatch.api.main import create_app
from nemwatch.config import Settings


def test_regions_returns_all_supported_regions() -> None:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    response = TestClient(app).get("/api/v1/regions")
    assert response.status_code == 200
    assert [item["code"] for item in response.json()] == ["QLD1", "NSW1", "VIC1", "SA1", "TAS1"]
