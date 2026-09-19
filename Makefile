.PHONY: up down logs ps migrate ingest demo test build verify processor-logs

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs --tail=200

ps:
	docker compose ps

migrate:
	docker compose run --rm api uv run alembic upgrade head

ingest:
	docker compose run --rm api python -m nemwatch.commands.load_fixture

demo: up migrate ingest
	@echo Dashboard: http://localhost:5173
	@echo Grafana: http://localhost:3000

processor-logs:
	docker compose logs --tail=200 processor

test:
	docker compose run --rm api uv run pytest -v
	docker compose run --rm frontend npm run test:run

build:
	docker compose build
	docker compose run --rm frontend npm run build

verify: migrate ingest
	docker compose config --quiet
	docker compose run --rm api uv run pytest -v
	docker compose run --rm api uv run ruff check src tests
	docker compose run --rm frontend npm run test:run
	docker compose run --rm frontend npm run build
	docker compose run --rm browser
