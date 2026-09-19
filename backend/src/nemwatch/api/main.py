from fastapi import FastAPI
from pydantic import ValidationError

from nemwatch.api.health import router as health_router
from nemwatch.config import Settings


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

    app = FastAPI(title="NEMWatch API", version="0.1.0")
    app.state.settings = active_settings
    app.include_router(health_router)
    return app
