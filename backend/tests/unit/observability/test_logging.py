import json
import logging

from nemwatch.observability.logging import JsonFormatter


def test_json_logging_redacts_sensitive_fields() -> None:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "handled", (), None)
    record.event = "request_handled"
    record.password = "sentinel-secret"
    body = json.loads(JsonFormatter("nemwatch-test").format(record))
    assert body["event"] == "request_handled"
    assert body["password"] == "[REDACTED]"
    assert "sentinel-secret" not in json.dumps(body)
