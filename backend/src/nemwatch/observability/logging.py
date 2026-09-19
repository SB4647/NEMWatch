import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
SENSITIVE_TERMS = ("password", "secret", "token", "authorization", "cookie", "connection_string", "database_url")
STANDARD = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}


def redact(value: Any, key: str = "") -> Any:
    if any(term in key.lower() for term in SENSITIVE_TERMS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str) -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        body: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "service": self.service_name,
            "event": getattr(record, "event", record.getMessage()),
            "correlation_id": correlation_id.get(),
        }
        for key, value in record.__dict__.items():
            if key not in STANDARD and key not in {"event"} and not key.startswith("_"):
                body[key] = redact(value, key)
        if record.exc_info:
            body["exception"] = record.exc_info[0].__name__
        return json.dumps(redact(body), separators=(",", ":"), default=str)


def configure_logging(service_name: str, level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service_name))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
