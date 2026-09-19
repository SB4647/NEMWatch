from pathlib import Path

import pytest
from pydantic import ValidationError

from nemwatch.api.main import create_app
from nemwatch.config import Settings


def test_missing_required_settings_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing = {item["loc"][0] for item in error.value.errors()}
    assert missing == {"database_url", "kafka_bootstrap_servers"}
    assert "password" not in str(error.value).lower()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("database_url", ""),
        ("database_url", "   "),
        ("kafka_bootstrap_servers", ""),
        ("kafka_bootstrap_servers", "   "),
    ],
)
def test_required_settings_reject_blank_values(field: str, value: str) -> None:
    values = {
        "database_url": "postgresql://nemwatch:secret@postgres:5432/nemwatch",
        "kafka_bootstrap_servers": "redpanda:9092",
    }
    values[field] = value

    with pytest.raises(ValidationError) as error:
        Settings(**values)

    invalid = {item["loc"][0] for item in error.value.errors()}
    assert invalid == {field}


@pytest.mark.parametrize(
    ("missing_env", "present_env", "missing_field"),
    [
        ("DATABASE_URL", "KAFKA_BOOTSTRAP_SERVERS", "database_url"),
        ("KAFKA_BOOTSTRAP_SERVERS", "DATABASE_URL", "kafka_bootstrap_servers"),
    ],
)
def test_startup_error_names_invalid_setting_without_leaking_other_value(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    missing_env: str,
    present_env: str,
    missing_field: str,
) -> None:
    sentinel = "sentinel-secret-value"
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(missing_env, raising=False)
    monkeypatch.setenv(present_env, sentinel)

    with pytest.raises(RuntimeError) as error:
        create_app()

    assert missing_field in str(error.value)
    assert sentinel not in str(error.value)
    assert error.value.__cause__ is None
