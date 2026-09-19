# Architecture

NEMWatch separates acquisition, event transport, processing, persistence, query APIs, and presentation so each boundary can fail and recover visibly.

```text
fixture/client -> ingestion -> Redpanda dispatch topic -> processor
                                                        |       |
                                                        v       v
                                                   PostgreSQL  alert topic
                                                        |       |
                                                        +--- FastAPI --- WebSocket --- Vue
```

## Domain and persistence

The domain package contains Pydantic models and event envelopes without framework or database imports. Decimal market values stay `Decimal` internally and serialize as strings. Timestamps must contain an offset and normalize to UTC.

SQLAlchemy repositories translate domain objects to PostgreSQL rows. `dispatch_observations` is unique on region and interval. `alerts` is unique on a key containing rule, region, and triggering interval. Replay creation takes a PostgreSQL advisory transaction lock so concurrent requests cannot both create active jobs.

## Delivery and transaction order

The processor disables Kafka auto-commit. For a valid dispatch event it:

1. Validates the versioned envelope.
2. Reads the preceding regional observation.
3. Upserts the current observation and evaluates enabled alert rules inside a database transaction.
4. Commits PostgreSQL.
5. Publishes newly inserted alert events.
6. Commits the consumed dispatch offset.

A database or alert-publication failure leaves the dispatch offset uncommitted. Retrying the message updates one observation and inserts each alert at most once. Invalid envelopes publish a redacted dead-letter record before their offsets advance.

## Live delivery

The API consumes dispatch and alert topics with its own consumer group. Each WebSocket has a bounded queue and sender task. A full queue disconnects only that slow client, so it cannot block persistence, processor consumption, or other browsers. Alert acknowledgements commit to PostgreSQL before broadcasting their state change.

## Replay

Replay parses the attributed fixture, filters regions, orders records by interval and region, and calls the standard event producer. It persists progress after every interval group and checks cancellation around delays and publishes. Repeating the source exercises the normal idempotency path.

## Health and telemetry

`/health/live` depends only on the API process. `/health/ready` checks PostgreSQL and Redpanda concurrently with short timeouts. JSON logs carry safe correlation context. Prometheus labels use bounded route templates, rule keys, regions, topics, and outcomes rather than raw URLs or identifiers.

## Local topology

Docker Compose runs PostgreSQL, Redpanda, API, processor, frontend, Prometheus, and Grafana. Published ports bind to `127.0.0.1`, application containers run as non-root users, and the browser test is isolated behind the `test` Compose profile.
