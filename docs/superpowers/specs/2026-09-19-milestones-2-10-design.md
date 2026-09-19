# NEMWatch Milestones 2–10 Local MVP Design

**Date:** 2026-09-19  
**Status:** Approved in conversation; written review pending  
**Scope:** Complete the required local MVP after the Milestone 1 runtime foundation

## Purpose

NEMWatch will become a recruiter-ready, event-driven educational application for public Australian National Electricity Market data. The completed local MVP will ingest a deterministic attributed fixture, convert valid rows into versioned events, persist regional observations idempotently, evaluate operational alert rules, expose REST and WebSocket interfaces, support historical replay, and present the result in an accessible Vue dashboard.

The application remains educational. It is not a trading, dispatch, or operational control system. It must contain only public or synthetic development data and must never use employer data.

## User direction and execution model

The attached project guide supplies product requirements, milestone scope, architecture, and completion criteria. Its instructions to stop for approval and run comprehensive tests after every milestone are superseded by Stephen's later direct request for a faster build-first workflow.

Milestones 2–10 will be implemented sequentially and committed separately. During implementation, checks are limited to those needed to prevent obvious syntax, import, schema, or build breakage. The complete backend, frontend, integration, streaming, browser, security, and clean-clone suites run once after all milestone code is present. Failures are fixed during one final stabilization phase.

No subagents or repeated independent review passes are part of this execution unless Stephen asks for them.

## Architectural direction

The system retains the event flow established in the project guide:

```text
AEMO fixture or public source
        |
        v
   ingestion service
        |
        v
Redpanda topic: nem.dispatch.observed.v1
        |
        v
   processor service
        |
        +----> PostgreSQL observations and alerts
        |
        +----> Redpanda topic: nem.alert.raised.v1
                         |
                         v
                FastAPI WebSocket hub
                         |
                         v
                    Vue dashboard
```

FastAPI also reads PostgreSQL through repository interfaces for REST queries. Historical replay publishes through the normal dispatch event producer so live and replayed data follow the same processing path.

## Backend boundaries

### Domain

`nemwatch.domain` contains Pydantic models, enums, protocols, event schemas, and pure alert rules. It does not import FastAPI, SQLAlchemy, Kafka clients, or PostgreSQL drivers.

Core types:

- `DispatchRecord`: region, aware interval timestamp, decimal price, demand, optional generation and interchange, source file, and source row.
- `AlertRule`: rule identifier, type, enabled state, threshold, optional region filter, and rule-specific configuration.
- `Alert`: stable identifier, rule, region, interval, severity, message, observed value, threshold, creation time, acknowledgement time, and acknowledgement note.
- `ReplayJob`: source, selected regions, speed, state, progress counters, start/end times, and cancellation state.
- `RejectedRow`: source row, machine-readable reason code, safe message, and non-secret row context.
- `DispatchObservedV1` and `AlertRaisedV1`: versioned envelopes with UUID event and correlation identifiers, aware UTC timestamps, stable event types, and typed payloads.

Decimal values remain strings at JSON boundaries and `Decimal` internally. All timestamps must be timezone-aware and normalized to UTC. Supported regions are `QLD1`, `NSW1`, `VIC1`, `SA1`, and `TAS1`.

### Persistence

SQLAlchemy 2 async models and Alembic manage PostgreSQL. The initial schema contains:

- `dispatch_observations`, unique on `(region, interval_datetime)`.
- `alert_rules`, with a stable unique rule key.
- `alerts`, with an idempotency key derived from rule, region, and triggering interval.
- `replay_jobs`, with status and progress fields.

Repositories expose domain objects and own all ORM translation. Dispatch upserts update mutable observation fields while preserving one row per region and interval. Alert inserts use their idempotency key to avoid duplicates. History queries always enforce region, date, ordering, and limit bounds.

### Ingestion

The checked-in fixture is a small CSV derived from a cited public AEMO dispatch source. Its adjacent attribution document records the public URL, retrieval date, selected fields, and any normalization applied.

`AemoClient` supports optional network ingestion with an identifying user agent, connection and read timeouts, bounded exponential retries, response-size limits, and visible failure results. The offline fixture path is the required demonstration path.

The parser recognizes only documented columns, validates each row independently, and returns valid records plus typed rejected rows. One invalid row cannot prevent valid rows from continuing. Unsupported regions, invalid timestamps, missing required fields, and malformed decimal values have distinct reason codes.

### Streaming and processing

The broker adapter uses an asyncio-compatible Kafka client against Redpanda. Topic administration creates required topics idempotently for local development.

The ingestion producer keys dispatch events by region and interval. The processor consumes `nem.dispatch.observed.v1`, performs the observation upsert and alert evaluation within the database transaction boundary, publishes any alert events, and commits the broker offset only after successful persistence. Retrying an event must not multiply observations or alerts.

The processor is a separate Compose service with its own command and health signal. Poison events are logged with safe structured context and retained for inspection through a dead-letter topic rather than silently discarded.

### API and live updates

FastAPI exposes:

- `GET /api/v1/regions`
- `GET /api/v1/dispatch/latest`
- `GET /api/v1/dispatch/history`
- `GET /api/v1/alerts`
- `POST /api/v1/alerts/{id}/acknowledge`
- `POST /api/v1/replays`
- `GET /api/v1/replays/{id}`
- `DELETE /api/v1/replays/{id}`
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `WS /ws/market`

Pydantic request and response models generate the OpenAPI schema. Lists use explicit pagination. History requires a supported region, aware `start` and `end` timestamps, `start < end`, and a maximum range configured in settings. Invalid regions, excessive ranges, missing records, replay conflicts, and invalid acknowledgement notes return stable problem responses.

The WebSocket hub broadcasts dispatch observations, raised alerts, acknowledgement changes, and replay progress. Slow or disconnected clients cannot block persistence or broker consumption.

### Alerts

Three pure domain rules are required:

- High price: current regional price exceeds a configured threshold.
- Rapid demand change: absolute or percentage change from the previous regional observation exceeds a configured threshold.
- Stale data: the latest regional observation is older than a configured duration.

Rules produce deterministic candidates that the repository stores idempotently. Acknowledgement records an aware UTC timestamp and a trimmed user note. It does not delete or hide alert history.

### Replay

A replay job reads a fixture or approved historical file, filters selected regions, and publishes observations in interval order through the standard producer. Speed controls the delay between source intervals and supports a fast demonstration mode.

Only one replay may be active. Jobs expose total, processed, rejected, and published counts; current source interval; state; failure message; and cancellation state. Cancellation is cooperative and leaves already-published events intact. Replaying the same source produces the same stored observations and alerts.

## Frontend design

Vue uses one typed API module and focused feature modules rather than embedding fetch calls in components. The dashboard contains:

- A regional overview with current price, demand, generation, interchange, interval time, and freshness state.
- A history view with region and date controls, an accessible trend chart, and a table containing the same values.
- An alert list with filters, severity and acknowledgement state, plus an acknowledgement form.
- A replay control with fixture selection, region filters, speed, progress, cancel action, and one-active-job feedback.
- A live connection indicator and non-blocking update announcements.

Every asynchronous view has useful initial, loading, empty, error, and retry states. Controls use labels, keyboard operation, visible focus, adequate contrast, and semantic status messaging. Charts never carry information that is absent from their table alternative.

The current development disclaimer remains visible. The UI must not imply that fixture values are current market information.

## Observability and resilience

Backend services emit structured JSON logs with service name, timestamp, level, event name, correlation identifier, and safe context. Secrets and full connection strings are never logged.

Prometheus metrics cover:

- Ingestion duration and outcome.
- Parsed and rejected row counts.
- Published and processed event counts.
- Processing failures and dead-letter events.
- Consumer lag when available.
- Alerts raised by rule and region.
- Replay state and duration.
- API request count, latency, and status.
- WebSocket connection count.

Grafana is provisioned with a NEMWatch overview dashboard and Prometheus data source. `/health/live` remains process-only. `/health/ready` checks required PostgreSQL and broker connectivity with short timeouts and a non-secret component summary.

Retries are bounded and applied only to operations that are safe to repeat. Database or broker outages produce visible readiness failures and structured logs without falsifying liveness.

## Local runtime

Docker Compose expands to include:

- `postgres`
- `redpanda`
- `api`
- `processor`
- `frontend`
- `prometheus`
- `grafana`

An ingestion command and replay command run as explicit one-off Compose tasks or API operations rather than always-on hidden schedulers. All published ports remain loopback-only. Application containers run as non-root users.

Make targets include startup, shutdown, verification, fixture loading, replay demonstration, logs, and service status. The default demonstration requires only Git and Docker Desktop.

## Continuous integration and portfolio output

GitHub Actions runs backend unit and integration tests, frontend component tests, linting, builds, and the browser smoke test. Service containers provide PostgreSQL and Redpanda. Dependency caches may accelerate jobs but must not bypass lockfiles.

Playwright verifies the primary demonstration: load known fixture data, open the regional dashboard, start a replay, observe an update, open the expected alert, acknowledge it, and confirm the state change.

The README leads with a final dashboard screenshot, the educational disclaimer, a one-command local demonstration, architecture and event flow, reliability choices, test strategy, operational URLs, trade-offs, and known limits. Screenshots must be generated from the deterministic fixture demonstration.

## Milestone delivery slices

### Milestone 2 Domain model and database

Add domain types, async database configuration, SQLAlchemy models, Alembic migrations, and repositories. Duplicate region and interval observations update one row.

### Milestone 3 AEMO parsing and fixture ingestion

Add the attributed public fixture, optional resilient client, parser, rejected-row results, and fixture-load command. The fixture has deterministic valid and rejected counts.

### Milestone 4 REST API

Add region, latest dispatch, bounded history, and alerts endpoints with typed schemas, pagination, stable validation errors, and repository dependencies.

### Milestone 5 Vue dashboard

Add the typed client, overview, history visualization and table, alert list, accessibility states, and fixture-data presentation.

### Milestone 6 Event streaming

Add topic administration, event envelopes, producer, processor service, post-transaction offset commits, dead-letter handling, and idempotent processing.

### Milestone 7 Alerts and live updates

Add the three rule engines, idempotent alert persistence, acknowledgement API, alert events, WebSocket broadcasting, and live dashboard behavior.

### Milestone 8 Historical replay

Add replay jobs, filters, speed, progress, cancellation, one-active-job enforcement, standard-producer reuse, and replay controls.

### Milestone 9 Observability and resilience

Add structured logs, correlation handling, metrics, readiness, retry and outage behavior, Prometheus, Grafana provisioning, and an overview dashboard.

### Milestone 10 Continuous integration and portfolio finish

Add GitHub Actions, Playwright smoke coverage, deterministic demo commands, screenshots, architecture and trade-off documentation, and the final clean-clone workflow.

## Consolidated verification strategy

Implementation checkpoints may use import, compile, migration-render, TypeScript, and Compose-configuration checks when needed. They do not repeat the complete suite.

After Milestone 10, stabilization runs:

1. Backend unit tests for domain, ingestion, API, streaming, processing, replay, and telemetry.
2. PostgreSQL repository and API integration tests.
3. Redpanda publish, consume, retry, and idempotency integration tests.
4. Frontend component tests and production build.
5. Playwright browser smoke test.
6. Prometheus and Grafana provisioning checks.
7. Broker and database outage readiness checks.
8. Credential, generated-file, and container-user hygiene checks.
9. A complete demonstration and clean-clone acceptance run.

The final acceptance record reports exact counts and observed service health. No passing result is recorded until the consolidated suite has actually completed.

## Security and scope limits

- No AWS credentials, AWS resources, Terraform apply, EKS, managed Kafka, or paid infrastructure.
- No production identity system, multi-tenancy, billing, or trading automation.
- No employer, participant-private, or non-public operational data.
- Network ingestion remains optional; the offline fixture is authoritative for demonstration and testing.
- Local credentials are development-only, ignored where appropriate, and exposed only through loopback-bound ports.
- Logs, errors, metrics labels, screenshots, and fixtures contain no secrets.

## Completion criteria

Milestones 2–10 are complete when the full local MVP starts from a clean clone, the deterministic fixture passes through the Redpanda-backed event pipeline, PostgreSQL remains idempotent, the Vue dashboard shows current and historical observations, all three alert types are visible and acknowledgeable, replay produces live WebSocket updates, Prometheus and Grafana expose useful behavior, CI contains the full suite, the browser demonstration passes, and the repository contains no secrets or generated artifacts.
