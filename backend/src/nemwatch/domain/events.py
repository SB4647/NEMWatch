from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from nemwatch.domain.models import Alert, DispatchRecord, require_aware_utc


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    event_type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: Literal[1] = 1

    _utc_occurred_at = field_validator("occurred_at")(require_aware_utc)


class DispatchObservedV1(EventEnvelope):
    event_type: Literal["nem.dispatch.observed.v1"] = "nem.dispatch.observed.v1"
    payload: DispatchRecord


class AlertRaisedV1(EventEnvelope):
    event_type: Literal["nem.alert.raised.v1"] = "nem.alert.raised.v1"
    payload: Alert
