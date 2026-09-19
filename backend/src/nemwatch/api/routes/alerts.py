from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from nemwatch.api.dependencies import get_alert_repository
from nemwatch.api.problems import problem
from nemwatch.api.schemas import AcknowledgeRequest, AlertPage, AlertResponse
from nemwatch.domain.models import Region, Severity
from nemwatch.persistence.repositories import AlertRepository

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=AlertPage)
async def list_alerts(
    request: Request,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
    region: Region | None = None,
    severity: Severity | None = None,
    acknowledged: bool | None = None,
    limit: Annotated[int, Query(ge=1)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AlertPage:
    if limit > request.app.state.settings.history_max_limit:
        raise problem(422, "limit_too_large", "Alert limit is too large")
    alerts = await repository.list(
        region=region, severity=severity, acknowledged=acknowledged,
        limit=limit + 1, offset=offset,
    )
    return AlertPage(
        items=[AlertResponse.from_domain(item) for item in alerts[:limit]],
        limit=limit, offset=offset, has_more=len(alerts) > limit,
    )


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    request: Request,
    alert_id: UUID,
    body: AcknowledgeRequest,
    repository: Annotated[AlertRepository, Depends(get_alert_repository)],
) -> AlertResponse:
    alert = await repository.acknowledge(alert_id, body.note, datetime.now(UTC))
    if alert is None:
        raise problem(404, "alert_not_found", "Alert was not found")
    await repository.session.commit()
    await request.app.state.hub.broadcast({
        "type": "alert_acknowledged", "data": AlertResponse.from_domain(alert).model_dump(mode="json")
    })
    return AlertResponse.from_domain(alert)
