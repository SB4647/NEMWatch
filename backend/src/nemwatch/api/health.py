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
