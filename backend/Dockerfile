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

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "nemwatch.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
