from typing import Annotated

from pydantic import StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

NonBlankString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    database_url: NonBlankString
    kafka_bootstrap_servers: NonBlankString
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
