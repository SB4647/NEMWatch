from uuid import uuid4

from fastapi.testclient import TestClient

from nemwatch.api.main import create_app
from nemwatch.config import Settings
from nemwatch.replay.service import ReplayConflict


class ConflictingReplayService:
    async def start(self, source, regions, speed):
        raise ReplayConflict


def test_second_replay_returns_stable_conflict() -> None:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    app.state.replay_service = ConflictingReplayService()
    response = TestClient(app).post('/api/v1/replays', json={"regions": ["QLD1"], "speed": 100})
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "replay_active"


def test_invalid_replay_identifier_is_validation_error() -> None:
    app = create_app(Settings(database_url="postgresql://u:p@db/n", kafka_bootstrap_servers="broker:9092"))
    response = TestClient(app).get('/api/v1/replays/not-a-uuid')
    assert response.status_code == 422
