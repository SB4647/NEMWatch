from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from math import isfinite
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Region(StrEnum):
    QLD1 = "QLD1"
    NSW1 = "NSW1"
    VIC1 = "VIC1"
    SA1 = "SA1"
    TAS1 = "TAS1"


REGION_NAMES: dict[Region, str] = {
    Region.QLD1: "Queensland",
    Region.NSW1: "New South Wales",
    Region.VIC1: "Victoria",
    Region.SA1: "South Australia",
    Region.TAS1: "Tasmania",
}


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRuleType(StrEnum):
    HIGH_PRICE = "high_price"
    RAPID_DEMAND_CHANGE = "rapid_demand_change"
    STALE_DATA = "stale_data"


class ReplayStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


def require_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def require_finite_decimal(value: Decimal) -> Decimal:
    if not value.is_finite() or not isfinite(float(value)):
        raise ValueError("decimal must be finite")
    return value


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DispatchRecord(DomainModel):
    region: Region
    interval_datetime: datetime
    price: Decimal
    demand: Decimal
    generation: Decimal | None = None
    interchange: Decimal | None = None
    source_file: NonBlank
    source_row: int = Field(ge=1)

    _utc_interval = field_validator("interval_datetime")(require_aware_utc)
    _finite_values = field_validator(
        "price", "demand", "generation", "interchange"
    )(lambda value: None if value is None else require_finite_decimal(value))


class AlertRule(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    rule_key: NonBlank
    rule_type: AlertRuleType
    enabled: bool = True
    threshold: Decimal
    region: Region | None = None
    severity: Severity = Severity.WARNING
    config: dict[str, Any] = Field(default_factory=dict)

    _finite_threshold = field_validator("threshold")(require_finite_decimal)


class Alert(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    idempotency_key: NonBlank
    rule_key: NonBlank
    rule_type: AlertRuleType
    region: Region
    interval_datetime: datetime
    severity: Severity
    message: NonBlank
    observed_value: Decimal
    threshold: Decimal
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    acknowledged_at: datetime | None = None
    acknowledgement_note: str | None = Field(default=None, max_length=500)

    _utc_times = field_validator(
        "interval_datetime", "created_at", "acknowledged_at"
    )(lambda value: None if value is None else require_aware_utc(value))
    _finite_alert_values = field_validator("observed_value", "threshold")(
        require_finite_decimal
    )

    @field_validator("acknowledgement_note")
    @classmethod
    def trim_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("acknowledgement note must not be blank")
        return value


class ReplayJob(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    source: NonBlank
    regions: tuple[Region, ...]
    speed: float = Field(gt=0, le=1_000)
    status: ReplayStatus = ReplayStatus.PENDING
    total: int = Field(default=0, ge=0)
    processed: int = Field(default=0, ge=0)
    published: int = Field(default=0, ge=0)
    rejected: int = Field(default=0, ge=0)
    current_interval: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancel_requested: bool = False
    failure_message: str | None = None

    _utc_replay_times = field_validator(
        "current_interval", "started_at", "completed_at"
    )(lambda value: None if value is None else require_aware_utc(value))


class RejectedRow(DomainModel):
    source_row: int = Field(ge=1)
    reason_code: NonBlank
    message: NonBlank
    context: dict[str, str] = Field(default_factory=dict)
