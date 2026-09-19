from typing import Literal

import asyncio
from typing import Literal

from aiokafka.admin import AIOKafkaAdminClient
from fastapi import APIRouter, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel
from sqlalchemy import text

from nemwatch.observability.metrics import READINESS

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["nemwatch-api"]


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse(status="ok", service="nemwatch-api")


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    components: dict[str, Literal["up", "down"]]


async def _database_ready(request: Request) -> bool:
    try:
        async with request.app.state.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _broker_ready(request: Request) -> bool:
    settings = request.app.state.settings
    admin = AIOKafkaAdminClient(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        request_timeout_ms=int(settings.readiness_timeout_seconds * 1000),
        client_id="nemwatch-readiness",
    )
    try:
        await admin.start()
        await admin.list_topics()
        return True
    except Exception:
        return False
    finally:
        try:
            await admin.close()
        except Exception:
            pass


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(request: Request, response: Response) -> ReadinessResponse:
    timeout = request.app.state.settings.readiness_timeout_seconds
    try:
        database, broker = await asyncio.wait_for(
            asyncio.gather(_database_ready(request), _broker_ready(request)), timeout=timeout
        )
    except TimeoutError:
        database, broker = False, False
    components = {"postgres": "up" if database else "down", "redpanda": "up" if broker else "down"}
    READINESS.labels("postgres").set(int(database))
    READINESS.labels("redpanda").set(int(broker))
    if not all((database, broker)):
        response.status_code = 503
        return ReadinessResponse(status="not_ready", components=components)
    return ReadinessResponse(status="ready", components=components)


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
