# NEMWatch Learning Log

## Milestone 1 Local runtime foundation

### Concept

Liveness, readiness, and container health answer different questions. `/health/live` proves the FastAPI process can serve a request. PostgreSQL and Redpanda health checks prove those dependencies can accept their own protocol-level checks. A future `/health/ready` endpoint will combine dependency checks when the API actually requires them.

### Project example

Stopping PostgreSQL and Redpanda does not change `/health/live`; the API process remains alive. Docker Compose separately marks the stopped dependencies unavailable. This separation prevents an external dependency outage from incorrectly restarting a healthy API process.
