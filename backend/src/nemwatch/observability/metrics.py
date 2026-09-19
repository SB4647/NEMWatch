from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter("nemwatch_http_requests_total", "HTTP requests", ["method", "route", "status_class"])
HTTP_DURATION = Histogram("nemwatch_http_request_duration_seconds", "HTTP request latency", ["method", "route"])
INGESTION_ROWS = Counter("nemwatch_ingestion_rows_total", "Rows handled during ingestion", ["outcome"])
INGESTION_DURATION = Histogram("nemwatch_ingestion_duration_seconds", "Fixture ingestion duration")
EVENTS = Counter("nemwatch_events_total", "Event pipeline activity", ["stage", "topic", "outcome"])
CONSUMER_LAG = Gauge("nemwatch_consumer_lag", "Consumer lag when broker metadata is available", ["group", "topic", "partition"])
ALERTS = Counter("nemwatch_alerts_raised_total", "New alerts persisted", ["rule", "region"])
REPLAY_JOBS = Counter("nemwatch_replay_jobs_total", "Replay terminal outcomes", ["status"])
REPLAY_DURATION = Histogram("nemwatch_replay_duration_seconds", "Replay duration", ["status"])
WEBSOCKET_CONNECTIONS = Gauge("nemwatch_websocket_connections", "Connected live clients")
READINESS = Gauge("nemwatch_readiness", "Dependency readiness", ["component"])
