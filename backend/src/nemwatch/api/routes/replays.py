from uuid import UUID

from fastapi import APIRouter, Request

from nemwatch.api.problems import problem
from nemwatch.api.schemas import ReplayRequest, ReplayResponse
from nemwatch.replay.service import ReplayConflict

router = APIRouter(prefix="/api/v1/replays", tags=["replays"])


@router.post("", response_model=ReplayResponse, status_code=202)
async def start_replay(request: Request, body: ReplayRequest) -> ReplayResponse:
    try:
        job = await request.app.state.replay_service.start(body.source, body.regions, body.speed)
    except ReplayConflict:
        raise problem(409, "replay_active", "Another replay is already active") from None
    except FileNotFoundError:
        raise problem(404, "replay_source_not_found", "Replay source was not found") from None
    return ReplayResponse.from_domain(job)


@router.get("/{job_id}", response_model=ReplayResponse)
async def get_replay(request: Request, job_id: UUID) -> ReplayResponse:
    job = await request.app.state.replay_service.get(job_id)
    if job is None:
        raise problem(404, "replay_not_found", "Replay job was not found")
    return ReplayResponse.from_domain(job)


@router.delete("/{job_id}", response_model=ReplayResponse)
async def cancel_replay(request: Request, job_id: UUID) -> ReplayResponse:
    job = await request.app.state.replay_service.cancel(job_id)
    if job is None:
        raise problem(404, "replay_not_found", "Replay job was not found")
    return ReplayResponse.from_domain(job)
