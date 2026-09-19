from fastapi import FastAPI

from nemwatch.api.health import router as health_router
from nemwatch.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or Settings()  # type: ignore[call-arg]
    app = FastAPI(title="NEMWatch API", version="0.1.0")
    app.state.settings = active_settings
    app.include_router(health_router)
    return app
