from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DispatchObservationRow(Base):
    __tablename__ = "dispatch_observations"
    __table_args__ = (
        UniqueConstraint("region", "interval_datetime", name="uq_dispatch_region_interval"),
        Index("ix_dispatch_region_interval", "region", "interval_datetime"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    interval_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    demand: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    generation: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    interchange: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)


class AlertRuleRow(Base):
    __tablename__ = "alert_rules"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    rule_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    rule_type: Mapped[str] = mapped_column(String(40), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    threshold: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    region: Mapped[str | None] = mapped_column(String(8))
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class AlertRow(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_created_at", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    rule_key: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(40), nullable=False)
    region: Mapped[str] = mapped_column(String(8), nullable=False)
    interval_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    observed_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledgement_note: Mapped[str | None] = mapped_column(String(500))


class ReplayJobRow(Base):
    __tablename__ = "replay_jobs"
    __table_args__ = (Index("ix_replay_jobs_status", "status"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    regions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    speed: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_interval: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_message: Mapped[str | None] = mapped_column(Text)
