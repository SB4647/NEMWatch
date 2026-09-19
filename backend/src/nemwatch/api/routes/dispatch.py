from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from nemwatch.api.dependencies import get_dispatch_repository
from nemwatch.api.problems import problem
from nemwatch.api.schemas import DispatchPage, DispatchResponse
from nemwatch.domain.models import Region, require_aware_utc
from nemwatch.persistence.repositories import DispatchRepository

router = APIRouter(prefix="/api/v1/dispatch", tags=["dispatch"])


@router.get("/latest", response_model=list[DispatchResponse])
async def latest_dispatch(
    repository: Annotated[DispatchRepository, Depends(get_dispatch_repository)],
    region: Annotated[list[Region] | None, Query()] = None,
) -> list[DispatchResponse]:
    selected = list(dict.fromkeys(region or list(Region)))
    records = [await repository.get_latest(item) for item in selected]
    return [DispatchResponse.from_domain(record) for record in records if record is not None]


@router.get("/history", response_model=DispatchPage)
async def dispatch_history(
    request: Request,
    repository: Annotated[DispatchRepository, Depends(get_dispatch_repository)],
    region: Region,
    start: datetime,
    end: datetime,
    limit: Annotated[int | None, Query(ge=1)] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DispatchPage:
    try:
        start = require_aware_utc(start)
        end = require_aware_utc(end)
    except ValueError:
        raise problem(422, "invalid_timestamp", "History timestamps must include an offset") from None
    settings = request.app.state.settings
    if start >= end:
        raise problem(422, "invalid_range", "History start must be before end")
    if end - start > timedelta(days=settings.history_max_days):
        raise problem(422, "range_too_large", f"History range cannot exceed {settings.history_max_days} days")
    page_limit = limit or settings.history_default_limit
    if page_limit > settings.history_max_limit:
        raise problem(422, "limit_too_large", f"History limit cannot exceed {settings.history_max_limit}")
    records = await repository.get_history(region, start, end, page_limit + 1, offset)
    return DispatchPage(
        items=[DispatchResponse.from_domain(item) for item in records[:page_limit]],
        limit=page_limit, offset=offset, has_more=len(records) > page_limit,
    )
