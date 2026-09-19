from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import asyncio
from contextlib import suppress
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from nemwatch.api.health import router as health_router
from nemwatch.api.problems import install_problem_handlers
from nemwatch.api.routes.alerts import router as alerts_router
from nemwatch.api.routes.dispatch import router as dispatch_router
from nemwatch.api.routes.regions import router as regions_router
from nemwatch.api.routes.replays import router as replays_router
from nemwatch.api.routes.websocket import router as websocket_router
from nemwatch.config import Settings
from nemwatch.live.consumer import consume_market_events
from nemwatch.live.hub import ConnectionHub
from nemwatch.persistence.database import create_engine, create_session_factory
from nemwatch.replay.service import ReplayService
from nemwatch.streaming.producer import EventProducer
from nemwatch.streaming.topics import ensure_topics


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
        app.state.hub = ConnectionHub(active_settings.websocket_queue_size)
        await ensure_topics(active_settings)
        producer = EventProducer(active_settings)
        await producer.start()
        fixture_directory = Path(__file__).resolve().parents[3] / "data" / "fixtures"
        app.state.replay_service = ReplayService(
            app.state.session_factory, producer, app.state.hub, fixture_directory
        )
        stop_event = asyncio.Event()
        live_task = asyncio.create_task(
            consume_market_events(active_settings, app.state.hub, stop_event)
        )
        yield
        stop_event.set()
        live_task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await live_task
        await app.state.replay_service.shutdown()
        await producer.stop()
        await engine.dispose()

    app = FastAPI(title="NEMWatch API", version="0.1.0", lifespan=lifespan)
    app.state.settings = active_settings
    app.state.hub = ConnectionHub(active_settings.websocket_queue_size)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[active_settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Correlation-ID"],
    )
    install_problem_handlers(app)
    app.include_router(health_router)
    app.include_router(regions_router)
    app.include_router(dispatch_router)
    app.include_router(alerts_router)
    app.include_router(websocket_router)
    app.include_router(replays_router)
    return app
