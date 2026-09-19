# Milestone 1 Local Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the NEMWatch repository foundation so a clean clone starts FastAPI, Vue, PostgreSQL, and Redpanda locally and exposes a tested API liveness contract and accessible dashboard shell.

**Architecture:** Use a container-first monorepo with four Docker Compose services: `api`, `frontend`, `postgres`, and `redpanda`. The API and frontend implement only observable shell behaviour; PostgreSQL and Redpanda prove the future runtime dependencies are healthy without adding schemas, topics, ingestion, or market-data features early.

**Tech Stack:** Python 3.13, uv 0.12.17, FastAPI 0.141.1, Pydantic 2, Vue 3.5.43, TypeScript, Vite 8.3.0, Vitest 5.0.1, Node 24.21.0, PostgreSQL 16.15, Redpanda 26.1.10, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-09-19-milestone-1-local-runtime-design.md`

## Global Constraints

- The backend language is Python 3.13.
- The API framework is FastAPI with Pydantic 2.
- The frontend is Vue 3 with TypeScript and Vite.
- PostgreSQL 16 is the database runtime.
- Redpanda supplies a local Kafka-compatible broker.
- Docker Compose is the required local runtime and the canonical clean-clone path.
- Container images and application dependencies use explicit version tags or lockfiles; `latest` tags are not permitted.
- Local configuration comes from environment variables with safe development values in `.env.example`.
- `.env`, credentials, generated build output, caches, and local database data are excluded from Git.
- No AWS credentials, Terraform execution, Kubernetes configuration, live AEMO ingestion, or production authentication is added.
- Commit subjects include `milestone-1`, describe the delivered capability, and have bodies that record the change and verification.
- Implement with test-first cycles. Do not continue after an unexpected failure; diagnose it before changing implementation.

## Version References

The pins above were checked on 2026-09-19 against the official FastAPI release notes, Astral uv Docker guide, Docker Official Images for Node and PostgreSQL, Redpanda releases, and the npm package pages for Vue, Vite, the Vue Vite plugin, and Vitest. Lockfiles are the reproducibility authority after generation.

## File Structure

| Area | Files | Responsibility |
|---|---|---|
| Repository policy | `.editorconfig`, `.gitattributes`, `.gitignore`, `AGENTS.md` | Cross-platform formatting, ignored artifacts, and working rules |
| Runtime orchestration | `.env.example`, `docker-compose.yml`, `Makefile` | Local configuration, services, health checks, and commands |
| Backend | `backend/pyproject.toml`, `backend/uv.lock`, `backend/Dockerfile`, `backend/.dockerignore`, `backend/src/nemwatch/**`, `backend/tests/**` | Settings, FastAPI factory, liveness route, and tests |
| Frontend | `frontend/package.json`, `frontend/package-lock.json`, `frontend/Dockerfile`, `frontend/.dockerignore`, `frontend/index.html`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/src/**`, `frontend/tests/**` | Accessible dashboard shell, styling, build, and tests |
| Project docs | `README.md`, `LEARNING_LOG.md`, `docs/architecture.md`, `docs/data-source.md`, `docs/decisions/0001-container-first-local-runtime.md` | Operation, architecture, data boundaries, decision record, and learning evidence |
| Deferred areas | `observability/README.md`, `infra/README.md` | State ownership and prevent premature configuration |

## Review Focus

1. Missing `DATABASE_URL` or `KAFKA_BOOTSTRAP_SERVERS` must produce a validation error naming the setting without revealing another setting's value. Task 1 adds the settings test.
2. `/health/live` must remain independent of database and broker availability. Task 1 constructs the application with unreachable dependency URLs and verifies HTTP 200.
3. The shell must not imply live market data exists. Task 2 verifies the development-state label and disclaimer and verifies that no market-value output is rendered.
4. Compose must resolve all required variables from `.env.example` without unresolved `${...}` expressions. Task 3 renders the resolved configuration and scans it before startup.
5. A clean clone must run without host Python, uv, PostgreSQL, or Redpanda. Task 5 performs acceptance from a temporary clone using Docker commands only.

---

### Task 1: Tested FastAPI liveness foundation

**Files:**
- Create: `backend/.dockerignore`
- Create: `backend/Dockerfile`
- Create: `backend/pyproject.toml`
- Create: `backend/uv.lock`
- Create: `backend/src/nemwatch/__init__.py`
- Create: `backend/src/nemwatch/config.py`
- Create: `backend/src/nemwatch/api/__init__.py`
- Create: `backend/src/nemwatch/api/health.py`
- Create: `backend/src/nemwatch/api/main.py`
- Create: `backend/tests/unit/api/test_health.py`
- Create: `backend/tests/unit/test_config.py`

**Interfaces:**
- Consumes: environment variables `DATABASE_URL`, `KAFKA_BOOTSTRAP_SERVERS`, and optional `LOG_LEVEL`.
- Produces: `Settings`, `create_app(settings: Settings | None = None) -> FastAPI`, and `GET /health/live` returning `{"status":"ok","service":"nemwatch-api"}`.

- [ ] **Step 1: Create the backend project and failing contract tests**

Create `backend/pyproject.toml`:

```toml
[project]
name = "nemwatch"
version = "0.1.0"
description = "Local Australian electricity market monitoring platform"
requires-python = ">=3.13,<3.14"
dependencies = [
  "fastapi==0.141.1",
  "pydantic-settings>=2.10,<3",
  "uvicorn[standard]>=0.35,<1",
]

[dependency-groups]
dev = [
  "httpx>=0.28,<1",
  "pytest>=8.4,<9",
  "ruff>=0.12,<1",
]

[build-system]
requires = ["uv_build>=0.12.17,<0.13"]
build-backend = "uv_build"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
target-version = "py313"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Create `backend/tests/unit/api/test_health.py`:

```python
from fastapi.testclient import TestClient

from nemwatch.api.main import create_app
from nemwatch.config import Settings


def test_liveness_contract() -> None:
    settings = Settings(
        database_url="postgresql://user:pass@unreachable:5432/nemwatch",
        kafka_bootstrap_servers="unreachable:9092",
    )

    response = TestClient(create_app(settings)).get("/health/live")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"status": "ok", "service": "nemwatch-api"}
```

Create `backend/tests/unit/test_config.py`:

```python
import pytest
from pydantic import ValidationError

from nemwatch.config import Settings


def test_missing_required_settings_are_named(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("KAFKA_BOOTSTRAP_SERVERS", raising=False)

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing = {item["loc"][0] for item in error.value.errors()}
    assert missing == {"database_url", "kafka_bootstrap_servers"}
    assert "password" not in str(error.value).lower()
```

Create empty package markers at `backend/src/nemwatch/__init__.py` and `backend/src/nemwatch/api/__init__.py`.

- [ ] **Step 2: Generate the backend lockfile in the pinned uv container**

Run from the repository root:

```powershell
docker run --rm --volume "${PWD}/backend:/app" --workdir /app ghcr.io/astral-sh/uv:0.12.17-python3.13-trixie-slim uv lock
```

Expected: exit 0 and `backend/uv.lock` created with Python 3.13-compatible resolutions.

- [ ] **Step 3: Run the tests and verify the red state**

```powershell
docker run --rm --volume "${PWD}/backend:/app" --workdir /app ghcr.io/astral-sh/uv:0.12.17-python3.13-trixie-slim uv run pytest tests/unit -v
```

Expected: FAIL during collection because `nemwatch.api.main` and `nemwatch.config` do not exist.

- [ ] **Step 4: Implement settings and the liveness route**

Create `backend/src/nemwatch/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    kafka_bootstrap_servers: str
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
```

Create `backend/src/nemwatch/api/health.py`:

```python
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["nemwatch-api"]


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok", service="nemwatch-api")
```

Create `backend/src/nemwatch/api/main.py`:

```python
from fastapi import FastAPI

from nemwatch.api.health import router as health_router
from nemwatch.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings()  # type: ignore[call-arg]
    app = FastAPI(title="NEMWatch API", version="0.1.0")
    app.state.settings = active_settings
    app.include_router(health_router)
    return app
```

- [ ] **Step 5: Add the backend container definition**

Create `backend/Dockerfile`:

```dockerfile
FROM ghcr.io/astral-sh/uv:0.12.17-python3.13-trixie-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY src ./src
COPY tests ./tests
RUN uv sync --locked

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "nemwatch.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

Create `backend/.dockerignore`:

```text
.venv
__pycache__
.pytest_cache
.ruff_cache
*.pyc
```

- [ ] **Step 6: Run backend verification**

```powershell
docker run --rm --volume "${PWD}/backend:/app" --workdir /app ghcr.io/astral-sh/uv:0.12.17-python3.13-trixie-slim uv run pytest tests/unit -v
docker run --rm --volume "${PWD}/backend:/app" --workdir /app ghcr.io/astral-sh/uv:0.12.17-python3.13-trixie-slim uv run ruff check src tests
docker build --tag nemwatch-api:test backend
```

Expected: all unit tests pass, Ruff reports no errors, and the image builds successfully.

- [ ] **Step 7: Commit the backend foundation**

```powershell
git add backend
git commit -m "feat(milestone-1): add the API health foundation" -m "Add pinned Python packaging, validated environment settings, a dependency-independent liveness contract, unit tests, linting, and the FastAPI container image."
```

---

### Task 2: Accessible Vue dashboard shell

**Files:**
- Create: `frontend/.dockerignore`
- Create: `frontend/Dockerfile`
- Create: `frontend/index.html`
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/style.css`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/tests/App.spec.ts`
- Create: `frontend/tests/setup.ts`

**Interfaces:**
- Consumes: browser request on port 5173 and optional `VITE_API_BASE_URL` for later milestones.
- Produces: a semantic page containing the exact product heading, development-state label, and educational-use disclaimer.

- [ ] **Step 1: Create the frontend package and failing component test**

Create `frontend/package.json`:

```json
{
  "name": "nemwatch-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest",
    "test:run": "vitest run"
  },
  "dependencies": {
    "vue": "3.5.43"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "6.0.9",
    "@vue/test-utils": "2.4.6",
    "jsdom": "27.0.0",
    "typescript": "5.9.3",
    "vite": "8.3.0",
    "vitest": "5.0.1",
    "vue-tsc": "3.0.8"
  }
}
```

Create `frontend/tests/App.spec.ts`:

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import App from '../src/App.vue'

describe('App', () => {
  it('identifies the product and its current development state', () => {
    const wrapper = mount(App)

    expect(wrapper.get('h1').text()).toBe('NEMWatch')
    expect(wrapper.text()).toContain('Local development shell')
  })

  it('shows the educational-use disclaimer without fake market values', () => {
    const wrapper = mount(App)

    expect(wrapper.text()).toContain(
      'Educational use only. Not a trading, dispatch, or operational control system.',
    )
    expect(wrapper.find('[data-testid="market-value"]').exists()).toBe(false)
  })
})
```

Create `frontend/tests/setup.ts`:

```typescript
import { afterEach } from 'vitest'

afterEach(() => {
  document.body.replaceChildren()
})
```

Create `frontend/vite.config.ts`:

```typescript
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
  },
})
```

- [ ] **Step 2: Generate the frontend lockfile**

```powershell
docker run --rm --volume "${PWD}/frontend:/app" --workdir /app node:24.21.0-alpine3.24 npm install --package-lock-only
```

Expected: exit 0 and `frontend/package-lock.json` created.

- [ ] **Step 3: Run the component test and verify the red state**

```powershell
docker run --rm --volume "${PWD}/frontend:/app" --workdir /app node:24.21.0-alpine3.24 sh -c "npm ci && npm run test:run"
```

Expected: FAIL because `frontend/src/App.vue` does not exist.

- [ ] **Step 4: Implement the dashboard shell**

Create `frontend/src/App.vue`:

```vue
<script setup lang="ts">
const projectSummary = 'Australian National Electricity Market monitoring and alerting'
</script>

<template>
  <main class="shell">
    <section class="hero" aria-labelledby="page-title">
      <p class="eyebrow">Local development shell</p>
      <h1 id="page-title">NEMWatch</h1>
      <p class="summary">{{ projectSummary }}</p>
      <p class="disclaimer">
        Educational use only. Not a trading, dispatch, or operational control system.
      </p>
    </section>
  </main>
</template>
```

Create `frontend/src/main.ts`:

```typescript
import { createApp } from 'vue'

import App from './App.vue'
import './style.css'

createApp(App).mount('#app')
```

Create `frontend/src/style.css`:

```css
:root {
  color: #172033;
  background: #f4f7fb;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
}

* {
  box-sizing: border-box;
}

body {
  min-width: 320px;
  min-height: 100vh;
  margin: 0;
}

.shell {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: 2rem;
}

.hero {
  width: min(46rem, 100%);
  padding: clamp(2rem, 6vw, 4rem);
  border: 1px solid #cbd7e8;
  border-radius: 1rem;
  background: #ffffff;
  box-shadow: 0 1rem 3rem rgb(23 32 51 / 10%);
}

.eyebrow {
  margin: 0 0 0.75rem;
  color: #315f91;
  font-size: 0.875rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: clamp(2.75rem, 10vw, 5rem);
  letter-spacing: -0.05em;
}

.summary {
  max-width: 36rem;
  margin: 1rem 0 2rem;
  color: #3d4c63;
  font-size: clamp(1.125rem, 3vw, 1.5rem);
  line-height: 1.5;
}

.disclaimer {
  margin: 0;
  padding-top: 1.25rem;
  border-top: 1px solid #dbe3ef;
  color: #55647a;
  line-height: 1.6;
}

:focus-visible {
  outline: 3px solid #1769aa;
  outline-offset: 3px;
}
```

Create `frontend/src/vite-env.d.ts`:

```typescript
/// <reference types="vite/client" />
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content="NEMWatch local development dashboard" />
    <title>NEMWatch</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["vite/client", "vitest/globals"]
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.vue", "tests/**/*.ts", "vite.config.ts"]
}
```

- [ ] **Step 5: Add the frontend container definition**

Create `frontend/Dockerfile`:

```dockerfile
FROM node:24.21.0-alpine3.24

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY tests ./tests

EXPOSE 5173
CMD ["npm", "run", "dev"]
```

Create `frontend/.dockerignore`:

```text
node_modules
dist
coverage
.vite
```

- [ ] **Step 6: Run frontend verification**

```powershell
docker run --rm --volume "${PWD}/frontend:/app" --workdir /app node:24.21.0-alpine3.24 sh -c "npm ci && npm run test:run && npm run build"
docker build --tag nemwatch-frontend:test frontend
```

Expected: two component tests pass, TypeScript reports no errors, Vite produces `dist`, and the image builds.

- [ ] **Step 7: Commit the dashboard shell**

```powershell
git add frontend
git commit -m "feat(milestone-1): add the accessible dashboard shell" -m "Add the pinned Vue toolchain, semantic project shell, educational-use disclaimer, component tests, production build, and development container."
```

---

### Task 3: Docker Compose local topology

**Files:**
- Create: `.editorconfig`
- Create: `.env.example`
- Create: `.gitattributes`
- Create: `.gitignore`
- Create: `docker-compose.yml`
- Create: `Makefile`

**Interfaces:**
- Consumes: `.env` copied from `.env.example`; images produced by Tasks 1 and 2.
- Produces: host endpoints `5173`, `8000`, `5432`, `19092`, and `9644`; healthy `postgres` and `redpanda` services; stable internal names `postgres:5432` and `redpanda:9092`.

- [ ] **Step 1: Add cross-platform repository policy files**

Create `.editorconfig`:

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

Create `.gitattributes`:

```gitattributes
* text=auto eol=lf
*.ps1 text eol=crlf
```

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
node_modules/
dist/
coverage/
.vite/
.idea/
.vscode/
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Define safe local environment values**

Create `.env.example`:

```dotenv
POSTGRES_DB=nemwatch
POSTGRES_USER=nemwatch
POSTGRES_PASSWORD=nemwatch_local_only
DATABASE_URL=postgresql://nemwatch:nemwatch_local_only@postgres:5432/nemwatch
KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
VITE_API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
```

Copy it locally without committing `.env`:

```powershell
Copy-Item .env.example .env
git check-ignore .env
```

Expected: `.env` is printed by `git check-ignore`, proving it is excluded.

- [ ] **Step 3: Create the Compose topology**

Create `docker-compose.yml`:

```yaml
name: nemwatch

services:
  postgres:
    image: postgres:16.15-alpine3.24
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 12
      start_period: 10s

  redpanda:
    image: docker.redpanda.com/redpandadata/redpanda:v26.1.10
    command:
      - redpanda
      - start
      - --smp
      - "1"
      - --memory
      - 1G
      - --reserve-memory
      - 0M
      - --overprovisioned
      - --node-id
      - "0"
      - --check=false
      - --kafka-addr
      - internal://0.0.0.0:9092,external://0.0.0.0:19092
      - --advertise-kafka-addr
      - internal://redpanda:9092,external://localhost:19092
      - --rpc-addr
      - 0.0.0.0:33145
      - --advertise-rpc-addr
      - redpanda:33145
    ports:
      - "19092:19092"
      - "9644:9644"
    volumes:
      - redpanda_data:/var/lib/redpanda/data
    healthcheck:
      test: ["CMD", "rpk", "cluster", "health", "--brokers=localhost:9092"]
      interval: 5s
      timeout: 5s
      retries: 12
      start_period: 15s

  api:
    build:
      context: ./backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      KAFKA_BOOTSTRAP_SERVERS: ${KAFKA_BOOTSTRAP_SERVERS}
      LOG_LEVEL: ${LOG_LEVEL}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redpanda:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live', timeout=2)"]
      interval: 5s
      timeout: 3s
      retries: 12
      start_period: 10s

  frontend:
    build:
      context: ./frontend
    environment:
      VITE_API_BASE_URL: ${VITE_API_BASE_URL}
    ports:
      - "5173:5173"
    depends_on:
      api:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:5173"]
      interval: 5s
      timeout: 3s
      retries: 12
      start_period: 10s

volumes:
  postgres_data:
  redpanda_data:
```

- [ ] **Step 4: Add convenience commands**

Create `Makefile` with real tab characters before each Docker command:

```makefile
.PHONY: up down logs ps test build verify

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs --tail=200

ps:
	docker compose ps

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
```

- [ ] **Step 5: Verify rendered configuration and required environment values**

```powershell
$resolved = docker compose --env-file .env.example config
$resolved | Select-String '\$\{'
if ($LASTEXITCODE -ne 0) { throw 'docker compose config failed' }
if ($resolved -match '\$\{') { throw 'Unresolved Compose variable found' }
docker compose --env-file .env.example config --services
```

Expected: no unresolved expression, and the service list is exactly `postgres`, `redpanda`, `api`, and `frontend`.

- [ ] **Step 6: Start the stack and verify health behaviour**

```powershell
docker compose up --build -d --wait
docker compose ps
curl.exe --fail --show-error http://localhost:8000/health/live
docker compose stop postgres redpanda
curl.exe --fail --show-error http://localhost:8000/health/live
docker compose up -d --wait postgres redpanda
```

Expected: all four services initially become healthy; both liveness requests return `{"status":"ok","service":"nemwatch-api"}`; stopping dependencies does not change liveness; PostgreSQL and Redpanda recover to healthy.

- [ ] **Step 7: Commit the local runtime topology**

```powershell
git add .editorconfig .env.example .gitattributes .gitignore docker-compose.yml Makefile
git commit -m "feat(milestone-1): compose the local service topology" -m "Add pinned PostgreSQL and Redpanda services, API and frontend orchestration, bounded health checks, safe local configuration, cross-platform repository rules, and repeatable developer commands."
```

---

### Task 4: Repository guidance and learning evidence

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `LEARNING_LOG.md`
- Create: `docs/architecture.md`
- Create: `docs/data-source.md`
- Create: `docs/decisions/0001-container-first-local-runtime.md`
- Create: `observability/README.md`
- Create: `infra/README.md`

**Interfaces:**
- Consumes: commands and endpoints implemented by Tasks 1-3.
- Produces: exact clean-clone instructions, contributor rules, architecture boundaries, data disclaimer, and the first learning entry.

- [ ] **Step 1: Write the operational README**

Create `README.md` with these exact sections and commands:

```markdown
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
```

- [ ] **Step 2: Record repository working rules**

Create `AGENTS.md`:

```markdown
# NEMWatch Working Rules

- Read the approved specification and implementation plan before changing a milestone.
- Explain the purpose, file list, and verification strategy before implementation.
- Use test-driven development for domain logic, parsing, repositories, APIs, and UI behaviour.
- Run the milestone's complete verification before reporting completion.
- Record one project example in `LEARNING_LOG.md` after every milestone.
- Commit completed checkpoints with a subject containing the milestone number and a descriptive body.
- Do not commit `.env`, credentials, employer data, generated build output, caches, or local volumes.
- Do not run `terraform apply`, provision AWS resources, create an EKS cluster, or deploy the project without a separate direct instruction from Stephen.
- Diagnose failures and report the observed evidence; never hide or skip a failing check.
```

- [ ] **Step 3: Write architecture, data, and decision documentation**

Create `docs/architecture.md` with the flow `AEMO -> ingestor -> Redpanda -> processor -> PostgreSQL -> FastAPI -> Vue`, clearly marking only Compose, service health, API liveness, and the Vue shell as implemented.

Create `docs/data-source.md` stating that NEMWatch will use only public AEMO data, must retain source attribution with checked-in fixtures, must not contain employer data, and is not an operational or trading system. State that the precise public dispatch file and fields will be documented when Milestone 3 adds the fixture.

Create `docs/decisions/0001-container-first-local-runtime.md` with status `Accepted`, date `2026-09-19`, context that host Python and uv are unavailable, decision that Docker Compose is canonical, consequences that clean-clone behaviour is reproducible but image pulls and Docker resources are required, and alternatives rejected: host-managed services and cloud-first deployment.

- [ ] **Step 4: Record the learning entry and deferred-area ownership**

Create `LEARNING_LOG.md`:

```markdown
# NEMWatch Learning Log

## Milestone 1 Local runtime foundation

### Concept

Liveness, readiness, and container health answer different questions. `/health/live` proves the FastAPI process can serve a request. PostgreSQL and Redpanda health checks prove those dependencies can accept their own protocol-level checks. A future `/health/ready` endpoint will combine dependency checks when the API actually requires them.

### Project example

Stopping PostgreSQL and Redpanda does not change `/health/live`; the API process remains alive. Docker Compose separately marks the stopped dependencies unavailable. This separation prevents an external dependency outage from incorrectly restarting a healthy API process.
```

Create `observability/README.md` stating that Milestone 9 owns Prometheus, Grafana, traces, structured logs, and outage exercises. Create `infra/README.md` stating that infrastructure is optional after the local MVP and no cloud resource may be created without separate approval.

- [ ] **Step 5: Verify documentation against the running system**

Run every README command exactly as written. Confirm each URL and service name matches `docker-compose.yml`, and run:

```powershell
rg -n "terraform apply|AWS|Educational use only|health/live|localhost:5173" README.md AGENTS.md LEARNING_LOG.md docs observability infra
git check-ignore .env backend/.venv frontend/node_modules frontend/dist
```

Expected: safeguards and URLs are discoverable, and every generated or sensitive path is ignored.

- [ ] **Step 6: Commit the documentation and learning evidence**

```powershell
git add README.md AGENTS.md LEARNING_LOG.md docs/architecture.md docs/data-source.md docs/decisions observability infra
git commit -m "docs(milestone-1): document the local runtime workflow" -m "Add clean-clone operating instructions, architecture and public-data boundaries, the container-first decision record, repository safeguards, deferred-area ownership, and the liveness-versus-readiness learning entry."
```

---

### Task 5: Clean-clone acceptance and recorded verification

**Files:**
- Modify: `LEARNING_LOG.md`

**Interfaces:**
- Consumes: the committed repository from Tasks 1-4.
- Produces: verified clean-clone evidence and the completion commit for the first milestone.

- [ ] **Step 1: Stop the working-copy stack and create an isolated clone**

```powershell
docker compose down
$acceptancePath = Join-Path $env:TEMP ("nemwatch-acceptance-" + [guid]::NewGuid().ToString("N"))
git clone . $acceptancePath
Copy-Item (Join-Path $acceptancePath '.env.example') (Join-Path $acceptancePath '.env')
Set-Location $acceptancePath
```

Expected: clone succeeds and contains no untracked files before `.env` is copied.

- [ ] **Step 2: Run the complete acceptance suite from the clone**

```powershell
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps
curl.exe --fail --show-error http://localhost:8000/health/live
docker compose run --rm api uv run pytest -v
docker compose run --rm api uv run ruff check src tests
docker compose run --rm frontend npm run test:run
docker compose run --rm frontend npm run build
```

Expected: Compose configuration succeeds; four services are healthy; liveness returns the exact JSON contract; backend tests, Ruff, frontend tests, type checking, and the production build all pass.

- [ ] **Step 3: Verify tracked-file hygiene**

```powershell
git status --short
git ls-files | Select-String -Pattern '(^|/)(\.env|node_modules|dist|\.venv|__pycache__)(/|$)'
```

Expected: only the ignored `.env` exists in the clone's working directory, `git status --short` prints nothing, and no prohibited generated path is tracked.

- [ ] **Step 4: Shut down the acceptance stack and return to the source repository**

```powershell
docker compose down
Set-Location 'C:\Users\steph\Software Projects\NEMWatch'
```

Keep the uniquely named temporary clone only until the milestone review is accepted; remove that exact path afterward.

- [ ] **Step 5: Record the observed acceptance result**

Append this section to `LEARNING_LOG.md` only after every command in Step 2 passes:

```markdown
### Verification

- `docker compose config --quiet`: PASS - the four-service topology resolved without missing variables.
- `docker compose up --build -d --wait`: PASS - PostgreSQL, Redpanda, FastAPI, and Vue reached healthy state from a clean clone.
- API liveness: PASS - returned `{"status":"ok","service":"nemwatch-api"}`.
- Backend unit tests and Ruff: PASS - all checks completed without failures.
- Frontend component tests and production build: PASS - all checks completed without failures.
- Git hygiene: PASS - no environment files, dependencies, caches, build output, or local volumes are tracked.
```

If any command fails, do not append PASS or create the completion commit; diagnose, fix in the owning task, and rerun the entire acceptance suite.

- [ ] **Step 6: Commit the verified completion record**

```powershell
git add LEARNING_LOG.md
git commit -m "chore(milestone-1): record clean-clone acceptance" -m "Record successful four-service startup, API liveness, backend checks, frontend tests and build, and tracked-file hygiene from an isolated clone."
```

- [ ] **Step 7: Present the review gate**

Show Stephen the final file list, commit list, exact test counts, service health output, and any limitations. Wait for explicit approval before designing or implementing Milestone 2.
