from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from nemwatch.domain.models import Alert, DispatchRecord, REGION_NAMES, Region, ReplayJob


def decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegionResponse(ApiModel):
    code: Region
    name: str

    @classmethod
    def all(cls) -> list["RegionResponse"]:
        return [cls(code=region, name=REGION_NAMES[region]) for region in Region]


class DispatchResponse(ApiModel):
    region: Region
    interval_datetime: datetime
    price: str
    demand: str
    generation: str | None
    interchange: str | None

    @classmethod
    def from_domain(cls, record: DispatchRecord) -> "DispatchResponse":
        return cls(
            region=record.region, interval_datetime=record.interval_datetime,
            price=decimal_text(record.price), demand=decimal_text(record.demand),
            generation=decimal_text(record.generation), interchange=decimal_text(record.interchange),
        )


class DispatchPage(ApiModel):
    items: list[DispatchResponse]
    limit: int
    offset: int
    has_more: bool


class AlertResponse(ApiModel):
    id: UUID
    rule_key: str
    rule_type: str
    region: Region
    interval_datetime: datetime
    severity: str
    message: str
    observed_value: str
    threshold: str
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledgement_note: str | None

    @classmethod
    def from_domain(cls, alert: Alert) -> "AlertResponse":
        return cls(
            id=alert.id, rule_key=alert.rule_key, rule_type=alert.rule_type.value,
            region=alert.region, interval_datetime=alert.interval_datetime,
            severity=alert.severity.value, message=alert.message,
            observed_value=decimal_text(alert.observed_value),
            threshold=decimal_text(alert.threshold), created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at,
            acknowledgement_note=alert.acknowledgement_note,
        )


class AlertPage(ApiModel):
    items: list[AlertResponse]
    limit: int
    offset: int
    has_more: bool


class AcknowledgeRequest(ApiModel):
    note: str = Field(min_length=1, max_length=500)

    @field_validator("note")
    @classmethod
    def trim_note(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("note must not be blank")
        return value


class ReplayResponse(ApiModel):
    id: UUID
    source: str
    regions: tuple[Region, ...]
    speed: float
    status: str
    total: int
    processed: int
    published: int
    rejected: int
    current_interval: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancel_requested: bool
    failure_message: str | None

    @classmethod
    def from_domain(cls, job: ReplayJob) -> "ReplayResponse":
        values = job.model_dump()
        values["status"] = job.status.value
        return cls(**values)
