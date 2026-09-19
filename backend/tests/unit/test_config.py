import pytest
from pydantic import ValidationError

from nemwatch.config import Settings


def test_missing_required_settings_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing = {item["loc"][0] for item in error.value.errors()}
    assert missing == {"database_url", "kafka_bootstrap_servers"}
    assert "password" not in str(error.value).lower()
