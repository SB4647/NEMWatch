from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from nemwatch.domain.models import (
    Alert,
    AlertRule,
    AlertRuleType,
    DispatchRecord,
    Region,
    ReplayJob,
    ReplayStatus,
    Severity,
)
from nemwatch.persistence.tables import AlertRow, AlertRuleRow, DispatchObservationRow, ReplayJobRow


def _dispatch(row: DispatchObservationRow) -> DispatchRecord:
    return DispatchRecord(
        region=Region(row.region), interval_datetime=row.interval_datetime, price=row.price,
        demand=row.demand, generation=row.generation, interchange=row.interchange,
        source_file=row.source_file, source_row=row.source_row,
    )


def _alert(row: AlertRow) -> Alert:
    return Alert(
        id=row.id, idempotency_key=row.idempotency_key, rule_key=row.rule_key,
        rule_type=AlertRuleType(row.rule_type), region=Region(row.region),
        interval_datetime=row.interval_datetime, severity=Severity(row.severity),
        message=row.message, observed_value=row.observed_value, threshold=row.threshold,
        created_at=row.created_at, acknowledged_at=row.acknowledged_at,
        acknowledgement_note=row.acknowledgement_note,
    )


def _replay(row: ReplayJobRow) -> ReplayJob:
    return ReplayJob(
        id=row.id, source=row.source, regions=tuple(Region(item) for item in row.regions),
        speed=float(row.speed), status=ReplayStatus(row.status), total=row.total,
        processed=row.processed, published=row.published, rejected=row.rejected,
        current_interval=row.current_interval, started_at=row.started_at,
        completed_at=row.completed_at, cancel_requested=row.cancel_requested,
        failure_message=row.failure_message,
    )


class DispatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, record: DispatchRecord) -> DispatchRecord:
        values = record.model_dump(mode="python")
        values["region"] = record.region.value
        statement = insert(DispatchObservationRow).values(**values)
        statement = statement.on_conflict_do_update(
            constraint="uq_dispatch_region_interval",
            set_={key: statement.excluded[key] for key in (
                "price", "demand", "generation", "interchange", "source_file", "source_row"
            )},
        ).returning(DispatchObservationRow)
        return _dispatch((await self.session.execute(statement)).scalar_one())

    async def get_latest(self, region: Region) -> DispatchRecord | None:
        query = select(DispatchObservationRow).where(
            DispatchObservationRow.region == region.value
        ).order_by(DispatchObservationRow.interval_datetime.desc()).limit(1)
        row = (await self.session.execute(query)).scalar_one_or_none()
        return None if row is None else _dispatch(row)

    async def get_previous(self, region: Region, before: datetime) -> DispatchRecord | None:
        query = select(DispatchObservationRow).where(
            DispatchObservationRow.region == region.value,
            DispatchObservationRow.interval_datetime < before,
        ).order_by(DispatchObservationRow.interval_datetime.desc()).limit(1)
        row = (await self.session.execute(query)).scalar_one_or_none()
        return None if row is None else _dispatch(row)

    async def get_history(
        self, region: Region, start: datetime, end: datetime, limit: int, offset: int = 0
    ) -> list[DispatchRecord]:
        query = select(DispatchObservationRow).where(
            DispatchObservationRow.region == region.value,
            DispatchObservationRow.interval_datetime >= start,
            DispatchObservationRow.interval_datetime <= end,
        ).order_by(DispatchObservationRow.interval_datetime).limit(limit).offset(offset)
        return [_dispatch(row) for row in (await self.session.execute(query)).scalars()]


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(
        self, *, region: Region | None = None, severity: Severity | None = None,
        acknowledged: bool | None = None, limit: int = 100, offset: int = 0,
    ) -> list[Alert]:
        query: Select[tuple[AlertRow]] = select(AlertRow)
        if region is not None:
            query = query.where(AlertRow.region == region.value)
        if severity is not None:
            query = query.where(AlertRow.severity == severity.value)
        if acknowledged is not None:
            query = query.where(AlertRow.acknowledged_at.is_not(None) if acknowledged else AlertRow.acknowledged_at.is_(None))
        query = query.order_by(AlertRow.created_at.desc()).limit(limit).offset(offset)
        return [_alert(row) for row in (await self.session.execute(query)).scalars()]

    async def insert_if_absent(self, alert: Alert) -> bool:
        values = alert.model_dump(mode="python")
        values.update(rule_type=alert.rule_type.value, region=alert.region.value, severity=alert.severity.value)
        result = await self.session.execute(
            insert(AlertRow).values(**values).on_conflict_do_nothing(
                index_elements=[AlertRow.idempotency_key]
            ).returning(AlertRow.id)
        )
        return result.scalar_one_or_none() is not None

    async def acknowledge(self, alert_id: UUID, note: str, acknowledged_at: datetime) -> Alert | None:
        statement = update(AlertRow).where(AlertRow.id == alert_id).values(
            acknowledgement_note=note.strip(), acknowledged_at=acknowledged_at
        ).returning(AlertRow)
        row = (await self.session.execute(statement)).scalar_one_or_none()
        return None if row is None else _alert(row)

    async def enabled_rules(self) -> list[AlertRule]:
        rows = (await self.session.execute(select(AlertRuleRow).where(AlertRuleRow.enabled.is_(True)))).scalars()
        return [AlertRule(
            id=row.id, rule_key=row.rule_key, rule_type=AlertRuleType(row.rule_type),
            enabled=row.enabled, threshold=row.threshold,
            region=None if row.region is None else Region(row.region),
            severity=Severity(row.severity), config=row.config,
        ) for row in rows]


class ReplayRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, job: ReplayJob) -> ReplayJob:
        values = job.model_dump(mode="python")
        values.update(regions=[region.value for region in job.regions], speed=str(job.speed), status=job.status.value)
        row = (await self.session.execute(insert(ReplayJobRow).values(**values).returning(ReplayJobRow))).scalar_one()
        return _replay(row)

    async def get(self, job_id: UUID) -> ReplayJob | None:
        row = await self.session.get(ReplayJobRow, job_id)
        return None if row is None else _replay(row)

    async def active(self) -> ReplayJob | None:
        query = select(ReplayJobRow).where(
            ReplayJobRow.status.in_([ReplayStatus.PENDING.value, ReplayStatus.RUNNING.value])
        ).order_by(ReplayJobRow.started_at.nullsfirst()).limit(1)
        row = (await self.session.execute(query)).scalar_one_or_none()
        return None if row is None else _replay(row)

    async def update(self, job_id: UUID, **changes: object) -> ReplayJob | None:
        if "status" in changes and isinstance(changes["status"], ReplayStatus):
            changes["status"] = changes["status"].value
        if "regions" in changes:
            changes["regions"] = [region.value for region in changes["regions"]]  # type: ignore[union-attr]
        row = (await self.session.execute(
            update(ReplayJobRow).where(ReplayJobRow.id == job_id).values(**changes).returning(ReplayJobRow)
        )).scalar_one_or_none()
        return None if row is None else _replay(row)
