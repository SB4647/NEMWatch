# NEMWatch

NEMWatch is an educational monitoring and alerting platform for public Australian National Electricity Market data. The current build provides the local service foundation; market ingestion begins in a later milestone.

> Educational use only. NEMWatch is not a trading, dispatch, or operational control system.

## Local prerequisites

- Docker Desktop with Linux containers
- Git
- At least 4 GB of memory available to Docker

Host Python, uv, Node, PostgreSQL, and Redpanda installations are not required.

## Start the local stack

```powershell
Copy-Item .env.example .env
docker compose config
docker compose up --build -d --wait
docker compose ps
```

## Local URLs

- Dashboard: http://localhost:5173
- API liveness: http://localhost:8000/health/live
- OpenAPI: http://localhost:8000/docs
- Redpanda admin API: http://localhost:9644

## Verify

```powershell
curl.exe --fail --show-error http://localhost:8000/health/live
docker compose run --rm api uv run pytest -v
docker compose run --rm api uv run ruff check src tests
docker compose run --rm frontend npm run test:run
docker compose run --rm frontend npm run build
```

## Stop

```powershell
docker compose down
```

Routine shutdown preserves local volumes. Delete volumes only when you explicitly want to discard local data.

## Current scope

The repository currently proves the local runtime, service health, API liveness contract, and dashboard shell. It does not yet contain live AEMO ingestion, database tables, Kafka topics, alerts, replay, AWS resources, or Kubernetes resources.
