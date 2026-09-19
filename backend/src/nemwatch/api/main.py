from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from nemwatch.api.health import router as health_router
from nemwatch.api.problems import install_problem_handlers
from nemwatch.api.routes.alerts import router as alerts_router
from nemwatch.api.routes.dispatch import router as dispatch_router
from nemwatch.api.routes.regions import router as regions_router
from nemwatch.config import Settings
from nemwatch.persistence.database import create_engine, create_session_factory


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        try:
            active_settings = Settings()  # type: ignore[call-arg]
        except ValidationError as error:
            invalid_settings = sorted(
                {".".join(str(part) for part in item["loc"]) for item in error.errors()}
            )
            raise RuntimeError(
                f"Invalid configuration settings: {', '.join(invalid_settings)}"
            ) from None
    else:
        active_settings = settings

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(active_settings)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        yield
        await engine.dispose()

    app = FastAPI(title="NEMWatch API", version="0.1.0", lifespan=lifespan)
    app.state.settings = active_settings
    install_problem_handlers(app)
    app.include_router(health_router)
    app.include_router(regions_router)
    app.include_router(dispatch_router)
    app.include_router(alerts_router)
    return app
