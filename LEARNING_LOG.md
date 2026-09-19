# NEMWatch Learning Log

## Milestone 3 Deterministic ingestion

### Concept

Batch ingestion should isolate bad input at the row boundary. One corrupt value becomes a typed rejection that can be counted and inspected without discarding valid observations that follow it.

### Project example

The checked-in fixture contains 15 valid observations and four deliberate errors. The parser returns all 15 records plus four reason-coded rejections without exposing full raw rows.

### Deferred verification

Parser, fixture-count, and client-boundary cases are checked in now. They run with the complete suite during consolidated stabilization.

## Milestone 2 Persistent market domain

### Concept

Idempotency belongs in the database boundary as well as application code. A PostgreSQL uniqueness constraint protects the invariant even when a message is retried, two workers race, or a caller bypasses an earlier duplicate check.

### Project example

`dispatch_observations` is unique on region and interval. The repository uses `ON CONFLICT DO UPDATE`, so receiving the same AEMO interval again refreshes its values while preserving a single observation.

### Deferred verification

Domain and repository cases are checked in with this milestone. Per the approved build-first workflow, the PostgreSQL integration suite runs during consolidated stabilization after Milestone 10.

## Milestone 1 Local runtime foundation

### Concept

Liveness, readiness, and container health answer different questions. `/health/live` proves the FastAPI process can serve a request. PostgreSQL and Redpanda health checks prove those dependencies can accept their own protocol-level checks. A future `/health/ready` endpoint will combine dependency checks when the API actually requires them.

### Project example

Stopping PostgreSQL and Redpanda does not change `/health/live`; the API process remains alive. Docker Compose separately marks the stopped dependencies unavailable. This separation prevents an external dependency outage from incorrectly restarting a healthy API process.

### Verification

- `docker compose config --quiet`: PASS - the four-service topology resolved without missing variables.
- `docker compose up --build -d --wait`: PASS - PostgreSQL, Redpanda, FastAPI, and Vue reached healthy state from a clean clone.
- API liveness: PASS - returned `{"status":"ok","service":"nemwatch-api"}`.
- Backend unit tests and Ruff: PASS - all checks completed without failures.
- Frontend component tests and production build: PASS - all checks completed without failures.
- Git hygiene: PASS - no environment files, dependencies, caches, build output, or local volumes are tracked.

### Review remediation

- Required configuration: PASS - blank values are rejected and startup errors name only invalid settings.
- Local access boundary: PASS - all published ports bind to `127.0.0.1`.
- Credential hygiene: PASS - common environment, key, certificate, AWS, and service-account paths are ignored.
- Container privileges: PASS - the API runs as UID 10001 and the frontend runs as UID 1000.
- Post-review clean clone: PASS - 8 backend tests, Ruff, 2 frontend tests, production build, service health, and Git hygiene all passed.
