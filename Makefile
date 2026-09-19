.PHONY: up down logs ps test build verify ingest processor-logs

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs --tail=200

ps:
	docker compose ps

ingest:
	docker compose run --rm api python -m nemwatch.commands.load_fixture

processor-logs:
	docker compose logs --tail=200 processor

test:
	docker compose run --rm api uv run pytest -v
	docker compose run --rm frontend npm run test:run

build:
	docker compose build
	docker compose run --rm frontend npm run build

verify:
	docker compose config --quiet
	docker compose run --rm api uv run pytest -v
	docker compose run --rm api uv run ruff check src tests
	docker compose run --rm frontend npm run test:run
	docker compose run --rm frontend npm run build
