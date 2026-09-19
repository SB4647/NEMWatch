# NEMWatch Milestones 2–10 Local MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the local NEMWatch MVP from persistent market observations through streaming, alerts, replay, observability, CI, and a portfolio-ready dashboard.

**Architecture:** A fixture-first ingestion path publishes versioned dispatch events to Redpanda. A separate processor persists idempotently to PostgreSQL, evaluates alert rules, and emits alert events; FastAPI exposes REST, readiness, metrics, and WebSocket interfaces consumed by a typed Vue dashboard. Historical replay reuses the standard producer, while Prometheus and Grafana observe the same local Compose system.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2 async, Alembic, asyncpg, aiokafka, PostgreSQL 16, Redpanda, Prometheus, Grafana, Vue 3, TypeScript 5.9, Vite 8, Vitest, Playwright, Docker Compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-19-milestones-2-10-design.md`

## Global Constraints

- Implement in the current working folder on `main`; do not create a worktree.
- Commit every milestone separately. Every subject contains the milestone number and every commit has a descriptive body.
- Follow Stephen's build-first direction: use only syntax, import, migration-render, TypeScript, and Compose checks during Milestones 2–10; run the complete suite once in Task 10.
- Do not use subagents or independent review passes unless Stephen asks for them.
- Python remains `>=3.13,<3.14`; Vue remains on the checked-in Vue 3 and TypeScript toolchain.
- Decimal values are strings at JSON boundaries and `Decimal` internally.
- Timestamps are timezone-aware and normalized to UTC.
- Supported regions are exactly `QLD1`, `NSW1`, `VIC1`, `SA1`, and `TAS1`.
- The deterministic offline fixture is the required demo source; network ingestion is optional.
- All published Compose ports bind to `127.0.0.1`; application containers run as non-root users.
- Never add AWS resources, paid infrastructure, employer data, production credentials, generated builds, caches, or local volumes.
- Record one concrete project lesson in `LEARNING_LOG.md` in every milestone commit.

## Review Focus

- Reprocessing the same `(region, interval_datetime)` must update one observation and must not multiply alerts; Task 1 defines repository tests and Task 10 executes them against PostgreSQL.
- A fixture containing malformed rows must publish every valid row and return a typed rejection for each invalid row; Task 2 defines parser tests and Task 10 runs them.
- An invalid or excessive history range must return a stable 422 problem response without querying an unbounded interval; Task 3 defines API tests and Task 10 executes them.
- A failed database transaction must leave the broker offset uncommitted, while a retry remains idempotent; Task 5 defines processor integration tests and Task 10 runs them with Redpanda.
- A slow WebSocket client or cancelled replay must not block processing or leave another replay permanently locked out; Tasks 6 and 7 define these tests and Task 10 executes them.

---

### Task 1: Milestone 2 — Domain model and PostgreSQL persistence

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/nemwatch/config.py`
- Create: `backend/src/nemwatch/domain/__init__.py`
- Create: `backend/src/nemwatch/domain/models.py`
- Create: `backend/src/nemwatch/domain/events.py`
- Create: `backend/src/nemwatch/persistence/__init__.py`
- Create: `backend/src/nemwatch/persistence/database.py`
- Create: `backend/src/nemwatch/persistence/tables.py`
- Create: `backend/src/nemwatch/persistence/repositories.py`
- Create: `backend/alembic.ini`
- Create: `backend/migrations/env.py`
- Create: `backend/migrations/script.py.mako`
- Create: `backend/migrations/versions/0001_initial_schema.py`
- Create: `backend/tests/unit/domain/test_models.py`
- Create: `backend/tests/integration/persistence/test_repositories.py`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Produces: `Region(StrEnum)`, `DispatchRecord`, `AlertRule`, `Alert`, `ReplayJob`, `RejectedRow`, `DispatchObservedV1`, and `AlertRaisedV1`.
- Produces: `create_engine(settings: Settings) -> AsyncEngine` and `create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]`.
- Produces: `DispatchRepository.upsert(record)`, `get_latest(region)`, `get_history(region, start, end, limit, offset)`; `AlertRepository.list(...)`, `insert_if_absent(alert)`, `acknowledge(alert_id, note, acknowledged_at)`; and `ReplayRepository.create/get/update/active`.

- [ ] **Step 1: Add persistence dependencies and configuration**

Run `uv add "sqlalchemy[asyncio]>=2.0,<3" "asyncpg>=0.30,<1" "alembic>=1.16,<2"` from `backend`. Extend `Settings` with bounded history and acknowledgement values:

```python
history_max_days: int = 31
history_default_limit: int = 500
history_max_limit: int = 5_000
acknowledgement_note_max_length: int = 500
```

- [ ] **Step 2: Define domain objects and event envelopes**

Implement frozen Pydantic models using `Decimal`, aware `datetime`, and UUID identifiers. Use these exact event headers:

```python
class EventEnvelope(BaseModel, frozen=True):
    event_id: UUID
    correlation_id: UUID
    event_type: str
    occurred_at: datetime
    schema_version: Literal[1] = 1

class DispatchObservedV1(EventEnvelope):
    event_type: Literal["nem.dispatch.observed.v1"] = "nem.dispatch.observed.v1"
    payload: DispatchRecord

class AlertRaisedV1(EventEnvelope):
    event_type: Literal["nem.alert.raised.v1"] = "nem.alert.raised.v1"
    payload: Alert
```

Validators reject naive timestamps, non-finite decimals, blank sources, unsupported regions, negative replay speed, and overlong acknowledgement notes.

- [ ] **Step 3: Add SQLAlchemy tables and session lifecycle**

Create async engine/session helpers and declarative rows for `dispatch_observations`, `alert_rules`, `alerts`, and `replay_jobs`. Store price, demand, generation, and interchange as `Numeric`; use timezone-aware database timestamps. Add unique constraints for `(region, interval_datetime)`, `rule_key`, and `alerts.idempotency_key`, plus indexes for regional history, alert creation time, and replay status.

- [ ] **Step 4: Add the initial Alembic migration**

Make `migrations/env.py` load `DATABASE_URL` through `Settings` and target the shared metadata. The migration creates all constraints and indexes from Step 3 and provides a complete downgrade in reverse dependency order.

- [ ] **Step 5: Implement repository behavior**

Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` for observations and `ON CONFLICT DO NOTHING` for alerts. `get_history` sorts ascending and applies both `limit` and `offset`. `acknowledge` trims the note, records the supplied UTC time, and returns `None` for an unknown UUID. `ReplayRepository.active()` recognizes `pending` and `running` only.

- [ ] **Step 6: Write deferred verification cases**

Add unit cases for timezone, decimal, region, and note validation. Add PostgreSQL integration cases for duplicate observation upsert, idempotent alert insert, ordered bounded history, unknown acknowledgement, acknowledgement persistence, and one active replay lookup. These tests are committed now and executed in Task 10.

- [ ] **Step 7: Run the lightweight checkpoint**

Run:

```powershell
uv run python -m compileall src migrations
uv run alembic upgrade head --sql | Out-Null
```

Expected: both commands exit `0`; no database container is started.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-2): add the persistent market domain

Define validated electricity-market models, versioned events, the initial PostgreSQL schema, and idempotent repository boundaries for observations, alerts, and replay jobs.
```

### Task 2: Milestone 3 — Fixture ingestion and resilient parsing

**Files:**
- Modify: `backend/src/nemwatch/config.py`
- Create: `backend/src/nemwatch/ingestion/__init__.py`
- Create: `backend/src/nemwatch/ingestion/aemo_client.py`
- Create: `backend/src/nemwatch/ingestion/parser.py`
- Create: `backend/src/nemwatch/ingestion/service.py`
- Create: `backend/src/nemwatch/commands/__init__.py`
- Create: `backend/src/nemwatch/commands/load_fixture.py`
- Create: `backend/data/fixtures/dispatch_sample.csv`
- Create: `backend/data/fixtures/ATTRIBUTION.md`
- Create: `backend/tests/unit/ingestion/test_parser.py`
- Create: `backend/tests/unit/ingestion/test_aemo_client.py`
- Modify: `docs/data-source.md`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: `DispatchRecord`, `RejectedRow`, `Region`.
- Produces: `ParseResult(records: tuple[DispatchRecord, ...], rejected: tuple[RejectedRow, ...])` and `parse_dispatch_csv(content: str, source: str) -> ParseResult`.
- Produces: `AemoClient.fetch(url: str) -> bytes` and `IngestionService.ingest_csv(content: str, source: str) -> IngestionResult`.

- [ ] **Step 1: Add the deterministic fixture and attribution**

Check in a small CSV with all five regions, sequential five-minute intervals, high-price and demand-jump triggers, plus deliberately malformed timestamp, decimal, region, and missing-field rows. `ATTRIBUTION.md` records the AEMO public page URL, retrieval date `2026-09-19`, selected columns, transformations, and the fact that malformed rows are synthetic test additions.

- [ ] **Step 2: Implement row-isolated parsing**

Map documented headers into `DispatchRecord`. Return these stable rejection codes: `missing_field`, `invalid_region`, `invalid_timestamp`, `invalid_decimal`, and `non_finite_decimal`. Catch errors per row and preserve the one-based source row number without logging the entire row.

- [ ] **Step 3: Implement bounded network retrieval**

Use standard-library HTTP in `asyncio.to_thread` with an identifying `User-Agent`, separate configured connection/read timeout values, a maximum response byte count, and three exponential attempts. Reject non-HTTPS URLs, redirects to non-HTTPS targets, oversized `Content-Length`, oversized streamed bodies, and non-2xx responses with typed `AemoClientError` messages that contain no credentials.

- [ ] **Step 4: Add fixture ingestion orchestration**

`IngestionService` parses content and accepts an injected `publish(record, correlation_id)` callable. It publishes valid rows in source order and returns valid, rejected, and published counts. `python -m nemwatch.commands.load_fixture` reads the checked-in fixture and prints one JSON summary object.

- [ ] **Step 5: Write deferred verification cases**

Pin the fixture's exact valid and rejection counts. Test that one bad row does not suppress following rows, each rejection code is stable, non-finite decimals fail, network retry is bounded, oversized responses fail, and the command summary contains no raw malformed row data.

- [ ] **Step 6: Run the lightweight checkpoint**

Run `uv run python -m compileall src tests`. Expected: exit `0`.

- [ ] **Step 7: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-3): add deterministic market ingestion

Add an attributed offline dispatch fixture, row-isolated validation, bounded optional HTTP retrieval, and a command path that reports valid, rejected, and published counts.
```

### Task 3: Milestone 4 — Typed REST API

**Files:**
- Modify: `backend/src/nemwatch/api/main.py`
- Modify: `backend/src/nemwatch/api/health.py`
- Create: `backend/src/nemwatch/api/dependencies.py`
- Create: `backend/src/nemwatch/api/problems.py`
- Create: `backend/src/nemwatch/api/schemas.py`
- Create: `backend/src/nemwatch/api/routes/regions.py`
- Create: `backend/src/nemwatch/api/routes/dispatch.py`
- Create: `backend/src/nemwatch/api/routes/alerts.py`
- Create: `backend/tests/unit/api/test_dispatch.py`
- Create: `backend/tests/unit/api/test_alerts.py`
- Create: `backend/tests/unit/api/test_regions.py`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: repository methods from Task 1.
- Produces: `get_session(request) -> AsyncIterator[AsyncSession]`, repository dependency providers, and REST routes under `/api/v1`.
- Produces: `ProblemDetail(code: str, message: str, fields: dict[str, str] | None)` wrapped as `{"detail": ...}`.

- [ ] **Step 1: Wire application lifespan and dependencies**

Create the engine and session factory during FastAPI lifespan, store them on `app.state`, and dispose the engine on shutdown. Dependency functions yield one async session per request and construct repositories without global mutable sessions.

- [ ] **Step 2: Add public response schemas**

Define schemas for region metadata, latest observations, paged history, paged alerts, and alert acknowledgement. Serialize every decimal as a string and every timestamp as an ISO-8601 UTC value. Page responses contain `items`, `limit`, `offset`, and `has_more`.

- [ ] **Step 3: Implement region and dispatch routes**

`GET /regions` returns all five stable region codes and names. `GET /dispatch/latest` accepts an optional repeated `region` query and returns available observations. `GET /dispatch/history` requires one region plus aware `start` and `end`, enforces `start < end`, `history_max_days`, and `history_max_limit`, then queries the repository.

- [ ] **Step 4: Implement alert routes**

`GET /alerts` supports optional region, severity, acknowledged, limit, and offset filters. `POST /alerts/{id}/acknowledge` accepts `{"note": "..."}`, trims the note, uses the current UTC time, returns the updated alert, and maps an unknown UUID to `404 alert_not_found`.

- [ ] **Step 5: Add stable error mapping**

Map unsupported regions, naive timestamps, reversed ranges, excessive ranges, invalid page values, and invalid notes to `422` problem bodies with stable codes. Unexpected persistence errors remain `500` and expose only a correlation ID.

- [ ] **Step 6: Write deferred verification cases**

Use repository fakes to test all routes without PostgreSQL. Include the Review Focus cases for reversed, naive, and 32-day history ranges, plus decimal serialization, pagination, empty latest results, filter forwarding, and unknown alert acknowledgement.

- [ ] **Step 7: Run the lightweight checkpoint**

Run `uv run python -c "from nemwatch.api.main import create_app; print(create_app)"`. Expected: a function representation and exit `0`.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-4): expose the market REST API

Add typed region, latest dispatch, bounded history, alert listing, and acknowledgement endpoints with stable validation problems and repository-backed dependencies.
```

### Task 4: Milestone 5 — Accessible Vue market dashboard

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/style.css`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/composables/useMarketDashboard.ts`
- Create: `frontend/src/components/StatusBanner.vue`
- Create: `frontend/src/components/RegionOverview.vue`
- Create: `frontend/src/components/HistoryPanel.vue`
- Create: `frontend/src/components/HistoryChart.vue`
- Create: `frontend/src/components/AlertList.vue`
- Create: `frontend/tests/api/client.spec.ts`
- Create: `frontend/tests/components/RegionOverview.spec.ts`
- Create: `frontend/tests/components/HistoryPanel.spec.ts`
- Create: `frontend/tests/components/AlertList.spec.ts`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: Task 3 REST schemas.
- Produces: `NemWatchClient` with `getRegions`, `getLatest`, `getHistory`, `getAlerts`, and `acknowledgeAlert` methods.
- Produces: `useMarketDashboard(client)` state with `regions`, `latest`, `history`, `alerts`, `selectedRegion`, `loading`, `error`, and explicit refresh actions.

- [ ] **Step 1: Define API types and one client**

Mirror backend response shapes in `api/types.ts`. `NemWatchClient` accepts `baseUrl` and an injectable `fetchFn`, URL-encodes query values, checks `response.ok`, parses problem responses, and throws `ApiError(status, code, message, fields)`.

- [ ] **Step 2: Build dashboard state orchestration**

Load regions, latest observations, and alerts together on startup. Load history when region or dates change. Protect each request with an incrementing token so slower stale responses cannot replace newer state. Expose retry actions without automatic unbounded retry loops.

- [ ] **Step 3: Build regional overview cards**

Render one semantic article per region with price, demand, generation, interchange, interval, and freshness. Use `data-state="fresh|stale|missing"`, textual freshness labels, and `aria-labelledby` rather than relying on color.

- [ ] **Step 4: Build accessible history controls and chart**

Provide labelled region, start, and end controls. Draw a dependency-free responsive SVG price line whose points have an accessible summary. Render the identical timestamp, price, and demand values in a captioned table below the chart.

- [ ] **Step 5: Build alert list and application shell**

Show severity, region, rule, message, observed value, threshold, time, and acknowledgement state. Keep the educational disclaimer at the top, add loading/empty/error/retry states, and use a polite live region for refresh results. The initial milestone presents acknowledgement state read-only; the form is added in Task 6 with live updates.

- [ ] **Step 6: Write deferred verification cases**

Cover URL encoding and problem parsing in the client, missing region data, matching chart/table values, labelled controls, keyboard-reachable retry, alert empty state, and visible educational disclaimer.

- [ ] **Step 7: Run the lightweight checkpoint**

Run `npm run build`. Expected: Vue type checking and Vite production build exit `0`. Remove `frontend/dist` after the check.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-5): build the accessible market dashboard

Add a typed API client, regional overview, equivalent history chart and table, alert states, and accessible loading, failure, and retry behavior.
```

### Task 5: Milestone 6 — Redpanda event pipeline and processor

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/nemwatch/config.py`
- Create: `backend/src/nemwatch/streaming/__init__.py`
- Create: `backend/src/nemwatch/streaming/topics.py`
- Create: `backend/src/nemwatch/streaming/producer.py`
- Create: `backend/src/nemwatch/streaming/consumer.py`
- Create: `backend/src/nemwatch/processing/__init__.py`
- Create: `backend/src/nemwatch/processing/service.py`
- Create: `backend/src/nemwatch/commands/run_processor.py`
- Create: `backend/tests/unit/streaming/test_serialization.py`
- Create: `backend/tests/integration/streaming/test_processor.py`
- Modify: `docker-compose.yml`
- Modify: `Makefile`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: `DispatchObservedV1`, persistence repositories, and `IngestionService` publisher callback.
- Produces: `EventProducer.start/stop/publish_dispatch/publish_alert`, `ensure_topics(bootstrap_servers)`, and `ProcessorService.run(stop_event)`.

- [ ] **Step 1: Add Kafka dependency and settings**

Run `uv add "aiokafka>=0.12,<1"` from `backend`. Add exact topic names, consumer group, dead-letter topic, request timeout, and maximum event byte settings. Keep `enable_auto_commit=False` in the consumer configuration.

- [ ] **Step 2: Implement deterministic event serialization**

Serialize Pydantic envelopes with UTF-8 JSON, sorted keys, ISO timestamps, UUID strings, and decimal strings. Use the UTF-8 key `region|interval_datetime` for dispatch messages and `rule_key|region|interval_datetime` for alert messages.

- [ ] **Step 3: Implement topic administration and producer lifecycle**

Create `nem.dispatch.observed.v1`, `nem.alert.raised.v1`, and `nem.events.dead-letter.v1` idempotently. The producer starts once, requires acknowledgements from all replicas, and flushes before stopping. Wire fixture ingestion to `publish_dispatch`.

- [ ] **Step 4: Implement processor transaction and offset order**

For each dispatch message: decode and validate, open a database transaction, upsert the observation, evaluate the injected alert evaluator, insert alerts idempotently, commit the database transaction, publish newly inserted alert events, then commit the exact consumed Kafka offset. Validation failures publish a redacted dead-letter record and commit only after that publish succeeds. Database or alert publish failures leave the offset uncommitted.

- [ ] **Step 5: Add the processor service to Compose**

Run `python -m nemwatch.commands.run_processor` as a separate non-root service using the API image. It depends on healthy PostgreSQL and Redpanda and exposes no host port. Add `make ingest`, `make processor-logs`, and topic initialization to the local workflow.

- [ ] **Step 6: Write deferred verification cases**

Test serialization round trips and stable keys. Against PostgreSQL and Redpanda, publish one event twice and assert one stored observation, inject a persistence failure and assert the offset remains retryable, and publish invalid JSON and assert one dead-letter record with no secret or raw connection value.

- [ ] **Step 7: Run the lightweight checkpoint**

Run:

```powershell
uv run python -m compileall src tests
docker compose config --quiet
```

Expected: both commands exit `0`; do not start the stack.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-6): add the durable dispatch pipeline

Publish versioned dispatch events through Redpanda, process them in a separate service, persist before committing offsets, and retain invalid events safely for inspection.
```

### Task 6: Milestone 7 — Alert rules, acknowledgement, and live updates

**Files:**
- Create: `backend/src/nemwatch/alerts/__init__.py`
- Create: `backend/src/nemwatch/alerts/rules.py`
- Create: `backend/src/nemwatch/live/__init__.py`
- Create: `backend/src/nemwatch/live/hub.py`
- Create: `backend/src/nemwatch/api/routes/websocket.py`
- Modify: `backend/src/nemwatch/api/routes/alerts.py`
- Modify: `backend/src/nemwatch/api/main.py`
- Modify: `backend/src/nemwatch/processing/service.py`
- Create: `backend/tests/unit/alerts/test_rules.py`
- Create: `backend/tests/unit/live/test_hub.py`
- Create: `backend/tests/unit/api/test_websocket.py`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/api/live.ts`
- Modify: `frontend/src/composables/useMarketDashboard.ts`
- Modify: `frontend/src/components/AlertList.vue`
- Create: `frontend/src/components/LiveStatus.vue`
- Create: `frontend/tests/components/LiveStatus.spec.ts`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Produces: `evaluate_alerts(current, previous, now, rules) -> tuple[AlertCandidate, ...]`.
- Produces: `ConnectionHub.connect/send/broadcast/disconnect` with bounded per-client queues.
- Produces: WebSocket message union `dispatch_observed | alert_raised | alert_acknowledged | replay_progress`.

- [ ] **Step 1: Implement three pure alert rules**

High price compares `current.price`; rapid demand change computes both absolute and percentage change when a previous nonzero demand exists; stale data compares `now - latest.interval_datetime`. Construct the idempotency key from rule key, region, and triggering interval. Disabled or region-filtered rules produce no candidate.

- [ ] **Step 2: Seed configurable rules and call them from processing**

Add deterministic default high-price, rapid-demand, and stale-data rules through the migration/repository layer. The processor reads enabled rules and the prior regional observation inside its transaction, inserts new alerts, and publishes `AlertRaisedV1` only for newly inserted rows.

- [ ] **Step 3: Implement the bounded WebSocket hub**

Each client gets a bounded `asyncio.Queue`. `broadcast` uses non-blocking enqueue; when a queue is full, close and remove that client. One sender task serializes messages per client. Disconnect cleanup cancels the sender and cannot propagate an exception into another connection.

- [ ] **Step 4: Connect REST changes and event consumption to live messages**

Add `/ws/market`. Start a background alert-topic consumer during API lifespan and broadcast received events. After acknowledgement commits, broadcast `alert_acknowledged`. Add a periodic stale-data evaluation loop with a bounded interval and clean shutdown.

- [ ] **Step 5: Add frontend live behavior and acknowledgement form**

`MarketSocket` reconnects with capped exponential delays and emits connection state. The dashboard merges messages by stable IDs, refreshes a region after dispatch updates, announces new alerts politely, and submits a labelled acknowledgement note form with disabled/success/error states.

- [ ] **Step 6: Write deferred verification cases**

Cover every rule at below/equal/above threshold, zero previous demand, filtered rules, and duplicate idempotency keys. Test slow-client eviction, disconnect cleanup, WebSocket message shape, acknowledgement live merge, and capped reconnection state.

- [ ] **Step 7: Run the lightweight checkpoint**

Run `uv run python -m compileall src tests` and `npm run build`; remove `frontend/dist`. Expected: both exit `0`.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-7): add live operational alerts

Evaluate high-price, rapid-demand, and stale-data rules idempotently, broadcast live market changes, and let dashboard users acknowledge alerts with notes.
```

### Task 7: Milestone 8 — Historical replay

**Files:**
- Create: `backend/src/nemwatch/replay/__init__.py`
- Create: `backend/src/nemwatch/replay/service.py`
- Create: `backend/src/nemwatch/api/routes/replays.py`
- Modify: `backend/src/nemwatch/api/schemas.py`
- Modify: `backend/src/nemwatch/api/main.py`
- Create: `backend/tests/unit/replay/test_service.py`
- Create: `backend/tests/unit/api/test_replays.py`
- Create: `backend/tests/integration/replay/test_replay_pipeline.py`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/components/ReplayControl.vue`
- Create: `frontend/tests/components/ReplayControl.spec.ts`
- Modify: `frontend/src/App.vue`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Produces: `ReplayService.start(request) -> ReplayJob`, `get(job_id)`, and `cancel(job_id)`.
- Produces: `POST /api/v1/replays`, `GET /api/v1/replays/{id}`, and `DELETE /api/v1/replays/{id}`.

- [ ] **Step 1: Define replay request and response contracts**

`ReplayRequest` contains `source="dispatch_sample.csv"`, one or more unique supported regions, and `speed` in `0.1..1000`. Responses expose status, total, processed, published, rejected, current interval, start/end time, cancellation flag, and safe failure message.

- [ ] **Step 2: Implement one-active replay orchestration**

Acquire a PostgreSQL advisory transaction lock before checking active jobs and creating a pending job. Reject a second job with `ReplayConflict`. Run the accepted job as a supervised application task, parse the fixture once, filter regions, sort by interval then region, and publish through `EventProducer.publish_dispatch`.

- [ ] **Step 3: Implement timing, progress, and cancellation**

Delay between source intervals by `source_delta / speed`, capped so cancellation checks occur at least every 250 ms. Persist progress after each interval group and broadcast `replay_progress`. Cancellation sets a database flag; the runner checks it before waits and publishes, then ends as `cancelled`. Exceptions end as `failed` with a redacted message.

- [ ] **Step 4: Add replay API routes**

Return `202` for accepted creation, `409 replay_active` for a conflict, `404 replay_not_found` for unknown jobs, current state from `GET`, and the updated cancelling/cancelled state from `DELETE`.

- [ ] **Step 5: Build replay dashboard controls**

Add region checkboxes, labelled speed input, start and cancel actions, progress counts, current interval, and terminal state. Disable start while a job is active and recover the active job after a page reload by polling only until the WebSocket connection resumes.

- [ ] **Step 6: Write deferred verification cases**

Use a fake clock and producer for ordering, filtering, speed delay, cancellation, and progress tests. Add concurrent API requests proving one accepted and one `409`. Add an end-to-end replay test proving repeated playback leaves one observation and one alert per idempotency key.

- [ ] **Step 7: Run the lightweight checkpoint**

Run `uv run python -m compileall src tests` and `npm run build`; remove `frontend/dist`. Expected: both exit `0`.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-8): add controlled historical replay

Replay filtered fixture history through the normal event producer with adjustable speed, durable progress, cooperative cancellation, and one-active-job enforcement.
```

### Task 8: Milestone 9 — Observability and resilience

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/nemwatch/config.py`
- Create: `backend/src/nemwatch/observability/__init__.py`
- Create: `backend/src/nemwatch/observability/logging.py`
- Create: `backend/src/nemwatch/observability/metrics.py`
- Create: `backend/src/nemwatch/observability/middleware.py`
- Modify: `backend/src/nemwatch/api/health.py`
- Modify: `backend/src/nemwatch/api/main.py`
- Modify: `backend/src/nemwatch/ingestion/service.py`
- Modify: `backend/src/nemwatch/processing/service.py`
- Modify: `backend/src/nemwatch/replay/service.py`
- Create: `backend/tests/unit/observability/test_logging.py`
- Create: `backend/tests/unit/observability/test_metrics.py`
- Create: `backend/tests/unit/api/test_readiness.py`
- Create: `observability/prometheus.yml`
- Create: `observability/grafana/provisioning/datasources/prometheus.yml`
- Create: `observability/grafana/provisioning/dashboards/dashboards.yml`
- Create: `observability/grafana/dashboards/nemwatch-overview.json`
- Modify: `observability/README.md`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Produces: `configure_logging(service_name, level)`, correlation-ID middleware, `/metrics`, and component-aware `/health/ready`.
- Produces: named Prometheus counters, histograms, and gauges for API, ingestion, processing, alerts, replay, and WebSockets.

- [ ] **Step 1: Add metrics dependency and structured logging**

Run `uv add "prometheus-client>=0.22,<1"` from `backend`. Implement a stdlib JSON formatter emitting timestamp, level, service, event, correlation ID, and safe structured fields. Add a redaction filter for keys containing password, secret, token, authorization, cookie, or connection-string terms.

- [ ] **Step 2: Add HTTP correlation and metrics middleware**

Accept a syntactically valid `X-Correlation-ID` up to 128 characters or generate a UUID. Return it in the response, bind it for downstream logs, and record request count and duration by route template, method, and status class without raw URL labels.

- [ ] **Step 3: Instrument pipeline behavior**

Record ingestion duration/outcomes, valid/rejected rows, published/processed/failure/dead-letter events, alerts by rule and region, replay state/duration, and WebSocket connections. Expose consumer lag only when broker metadata supplies it; absence must not fail metrics rendering.

- [ ] **Step 4: Implement liveness and readiness separation**

Keep `/health/live` process-only. `/health/ready` checks `SELECT 1` and broker metadata concurrently with short timeouts and returns `200 {status:"ready"}` or `503 {status:"not_ready", components:{postgres:"up|down", redpanda:"up|down"}}`. Responses contain no exception text or connection details.

- [ ] **Step 5: Provision Prometheus and Grafana**

Add loopback-only `9090` and `3000` services. Prometheus scrapes the API and processor metrics endpoints. Grafana provisions Prometheus plus panels for request rate/latency/errors, parsed/rejected rows, event throughput/failures, alerts, replay state, WebSockets, and readiness.

- [ ] **Step 6: Write deferred verification cases**

Test JSON parsing, correlation propagation, secret redaction, bounded metric labels, independent database/broker readiness failures, liveness during dependency failure, and a valid Prometheus exposition body.

- [ ] **Step 7: Run the lightweight checkpoint**

Run `uv run python -m compileall src tests` and `docker compose config --quiet`. Expected: both exit `0`; do not start the stack.

- [ ] **Step 8: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-9): add observable resilient services

Add safe JSON logs, correlation IDs, bounded Prometheus metrics, dependency-aware readiness, and provisioned local Prometheus and Grafana dashboards.
```

### Task 9: Milestone 10 — CI, browser demonstration, and portfolio finish

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/demo.spec.ts`
- Create: `.github/workflows/ci.yml`
- Modify: `Makefile`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Create: `docs/demo.md`
- Create: `docs/tradeoffs.md`
- Create: `docs/screenshots/.gitkeep`
- Modify: `infra/README.md`
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: the complete REST, WebSocket, replay, and Compose surface.
- Produces: `make demo`, `make verify`, Playwright `demo.spec.ts`, and GitHub Actions jobs `backend`, `frontend`, `integration`, and `browser`.

- [ ] **Step 1: Add Playwright and deterministic browser setup**

Run `npm install --save-dev @playwright/test` in `frontend`. Configure Chromium, trace on first retry, screenshot only on failure, and base URL `http://127.0.0.1:5173`. The smoke test loads the fixture, opens the dashboard, starts fast replay, waits for the expected high-price alert, acknowledges it with `Reviewed in browser smoke test`, and verifies the acknowledged state.

- [ ] **Step 2: Create stable demo and verification commands**

`make demo` starts the stack, migrates the database, initializes topics, loads the fixture, and prints the frontend/Grafana URLs. `make verify` runs backend unit/integration tests, Ruff, frontend Vitest/build, Playwright, Compose config, provisioning validation, and hygiene scripts exactly once.

- [ ] **Step 3: Add GitHub Actions**

Use lockfiles, Python 3.13, Node from the frontend toolchain, PostgreSQL and Redpanda service containers, and explicit health waits. Upload Playwright traces only on failure. Jobs run backend tests/lint, frontend tests/build, integration tests, and browser smoke; no cloud credentials or deployment permissions are present.

- [ ] **Step 4: Finish architecture and demo documentation**

README begins with the educational disclaimer, deterministic demo command, final dashboard image location, feature list, event flow, REST/WebSocket endpoints, operational URLs, and verification command. `docs/architecture.md` documents transaction/offset order and idempotency. `docs/demo.md` gives a five-minute walkthrough. `docs/tradeoffs.md` explains fixture-first data, at-least-once delivery, single-node local services, in-process WebSocket fanout, and excluded AWS/Kubernetes scope.

- [ ] **Step 5: Capture deterministic screenshots after the app works**

Capture dashboard overview, history, acknowledged alert, replay progress, and Grafana overview into `docs/screenshots/` with descriptive filenames and alt text references in README. Generated transient Playwright artifacts remain ignored.

- [ ] **Step 6: Run the lightweight checkpoint**

Run `docker compose config --quiet` and `npm run build`; remove `frontend/dist`. Expected: both exit `0`.

- [ ] **Step 7: Record the milestone commit**

Update `LEARNING_LOG.md`, then commit with:

```text
feat(milestone-10): complete the local portfolio workflow

Add CI, a deterministic browser demonstration, complete verification commands, screenshots, and reviewer-focused architecture, operations, and trade-off documentation.
```

### Task 10: Consolidated verification and stabilization

**Files:**
- Modify: only files required to correct observed failures
- Create: `docs/acceptance/2026-09-19-local-mvp.md`

**Interfaces:**
- Consumes: the completed Milestones 2–10 system.
- Produces: one evidence-backed acceptance record and, when necessary, focused fix commits that name the affected milestone.

- [ ] **Step 1: Install locked dependencies and start clean services**

Run `docker compose down -v`, rebuild from lockfiles, start the stack, run Alembic to `head`, and wait for PostgreSQL, Redpanda, API, processor, frontend, Prometheus, and Grafana health. Record container image IDs and health results.

- [ ] **Step 2: Run backend unit and integration verification**

Run:

```powershell
docker compose run --rm api uv run pytest -v
docker compose run --rm api uv run ruff check src tests
```

Expected: all tests and lint pass. For any failure, apply the smallest root-cause fix, rerun only the failing target, then rerun these two commands once.

- [ ] **Step 3: Run frontend verification**

Run component tests and the production build inside the frontend container. Expected: all Vitest cases pass, TypeScript reports no errors, and Vite exits `0`. Remove generated `dist` after recording the result.

- [ ] **Step 4: Run live integration and idempotency checks**

Load the fixture twice, verify stored observation and alert counts remain stable, run a fast replay twice, verify the same stable counts, acknowledge one alert, and confirm REST plus WebSocket state. Record exact valid, rejected, observation, and alert counts.

- [ ] **Step 5: Run outage and recovery checks**

Stop PostgreSQL and confirm liveness stays `200` while readiness becomes `503`; restore it and confirm readiness. Repeat for Redpanda. Confirm the processor resumes from its uncommitted offset and creates no duplicate row.

- [ ] **Step 6: Run observability and browser checks**

Verify Prometheus targets are up, required metric names have samples, Grafana provisioning endpoints report the data source/dashboard, then run the Playwright smoke test. Expected: the full replay-to-acknowledgement journey passes.

- [ ] **Step 7: Run security and repository hygiene checks**

Verify loopback-only port bindings, non-root application UIDs, ignored `.env`/credential patterns, no tracked caches/builds/volumes, no credential-like strings in tracked files, and no privileged containers. Inspect `git status --short` for only intentional acceptance changes.

- [ ] **Step 8: Run clean-clone acceptance**

Clone the current local repository into a temporary directory, copy `.env.example` to `.env`, run the documented demo and `make verify`, and confirm the same deterministic counts and healthy services. Shut down the temporary stack and remove its volumes after evidence is recorded.

- [ ] **Step 9: Write acceptance evidence and commit stabilization**

Record commands, versions, exact counts, health behavior, browser outcome, and any remaining known limitation in `docs/acceptance/2026-09-19-local-mvp.md`. If fixes or acceptance documentation changed the tree, commit with:

```text
fix(milestones-2-10): stabilize the complete local MVP

Resolve failures observed during consolidated backend, frontend, streaming, outage, browser, security, and clean-clone acceptance and record the verified results.
```

- [ ] **Step 10: Stop local services without deleting the primary volumes**

Run `docker compose down` in the main workspace and confirm `git status --short --branch` contains no uncommitted generated artifacts. Do not push; Stephen owns the repository push.
