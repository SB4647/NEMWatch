# Architecture

NEMWatch is designed around this event flow:

```text
AEMO -> ingestor -> Redpanda -> processor -> PostgreSQL -> FastAPI -> Vue
```

The ingestor will obtain public Australian Energy Market Operator data and publish normalized events to Redpanda. A processor will validate and enrich those events before persisting queryable state in PostgreSQL. FastAPI will expose that state to the Vue dashboard.

## Implemented in Milestone 1

- Docker Compose defines the PostgreSQL, Redpanda, FastAPI, and Vue services.
- Protocol-level health checks verify PostgreSQL and Redpanda.
- FastAPI exposes the dependency-independent `GET /health/live` contract.
- Vue renders an accessible local development shell with no market values.

## Planned boundaries

The ingestor, event schemas, processor, database schema, market-data APIs, alerts, replay, cloud infrastructure, and production observability are not implemented. Later milestones must preserve the flow above while keeping acquisition, event processing, storage, API, and presentation responsibilities separate.
