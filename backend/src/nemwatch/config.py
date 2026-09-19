from typing import Annotated

from pydantic import StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    database_url: NonBlankString
    kafka_bootstrap_servers: NonBlankString
    log_level: str = "INFO"
    history_max_days: int = 31
    history_default_limit: int = 500
    history_max_limit: int = 5_000
    acknowledgement_note_max_length: int = 500
    aemo_connect_timeout_seconds: float = 5.0
    aemo_read_timeout_seconds: float = 15.0
    aemo_max_response_bytes: int = 10_000_000
    aemo_user_agent: str = "NEMWatch/0.1 educational-project"
    frontend_origin: str = "http://localhost:5173"
    dispatch_topic: str = "nem.dispatch.observed.v1"
    alert_topic: str = "nem.alert.raised.v1"
    dead_letter_topic: str = "nem.events.dead-letter.v1"
    processor_consumer_group: str = "nemwatch-processor-v1"
    kafka_request_timeout_ms: int = 10_000
    kafka_max_event_bytes: int = 1_000_000
    live_consumer_group: str = "nemwatch-api-live-v1"
    websocket_queue_size: int = 100
    stale_check_interval_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
