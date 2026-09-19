# Observability

NEMWatch emits JSON logs with service, event, level, timestamp, correlation ID, and redacted structured context. The API exposes Prometheus metrics at `http://localhost:8000/metrics`; the processor exposes an internal Compose-only endpoint on port 9000.

Prometheus is available at `http://localhost:9090` and Grafana at `http://localhost:3000`. Grafana automatically provisions the Prometheus data source and the **NEMWatch overview** dashboard. Credentials come from the development-only `.env` file.

`/health/live` checks only the API process. `/health/ready` checks PostgreSQL and Redpanda independently with short timeouts and returns only `up` or `down` component states.
