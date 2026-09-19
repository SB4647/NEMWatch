import asyncio
from datetime import UTC, datetime
from itertools import groupby
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from nemwatch.domain.models import DispatchRecord, Region, ReplayJob, ReplayStatus
from nemwatch.ingestion.parser import parse_dispatch_csv
from nemwatch.live.hub import ConnectionHub
from nemwatch.persistence.repositories import ReplayRepository
from nemwatch.streaming.producer import EventProducer

REPLAY_LOCK_KEY = 0x4E454D57


class ReplayConflict(RuntimeError):
    pass


class ReplayService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        producer: EventProducer,
        hub: ConnectionHub,
        fixture_directory: Path,
    ) -> None:
        self.session_factory = session_factory
        self.producer = producer
        self.hub = hub
        self.fixture_directory = fixture_directory
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    async def start(self, source: str, regions: tuple[Region, ...], speed: float) -> ReplayJob:
        path = (self.fixture_directory / source).resolve()
        if path.parent != self.fixture_directory.resolve() or not path.is_file():
            raise FileNotFoundError(source)
        parsed = parse_dispatch_csv(path.read_text(encoding="utf-8"), source)
        records = sorted(
            (item for item in parsed.records if item.region in regions),
            key=lambda item: (item.interval_datetime, item.region.value),
        )
        job = ReplayJob(
            source=source, regions=regions, speed=speed,
            total=len(records), rejected=len(parsed.rejected),
        )
        async with self.session_factory() as session:
            repository = ReplayRepository(session)
            async with session.begin():
                await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": REPLAY_LOCK_KEY})
                if await repository.active() is not None:
                    raise ReplayConflict("A replay is already active")
                job = await repository.create(job)
        self._tasks[job.id] = asyncio.create_task(self._run(job, tuple(records)))
        return job

    async def get(self, job_id: UUID) -> ReplayJob | None:
        async with self.session_factory() as session:
            return await ReplayRepository(session).get(job_id)

    async def cancel(self, job_id: UUID) -> ReplayJob | None:
        async with self.session_factory() as session:
            async with session.begin():
                return await ReplayRepository(session).update(job_id, cancel_requested=True)

    async def shutdown(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)

    async def _run(self, job: ReplayJob, records: tuple[DispatchRecord, ...]) -> None:
        try:
            await self._update(job.id, status=ReplayStatus.RUNNING, started_at=datetime.now(UTC))
            previous_interval: datetime | None = None
            processed = 0
            published = 0
            for interval, group in groupby(records, key=lambda item: item.interval_datetime):
                if await self._cancel_requested(job.id):
                    await self._finish(job.id, ReplayStatus.CANCELLED)
                    return
                if previous_interval is not None:
                    await self._delay((interval - previous_interval).total_seconds() / job.speed, job.id)
                    if await self._cancel_requested(job.id):
                        await self._finish(job.id, ReplayStatus.CANCELLED)
                        return
                for record in group:
                    await self.producer.publish_dispatch(record, job.id)
                    processed += 1
                    published += 1
                previous_interval = interval
                updated = await self._update(
                    job.id, processed=processed, published=published, current_interval=interval
                )
                if updated is not None:
                    await self._broadcast(updated)
            await self._finish(job.id, ReplayStatus.COMPLETED)
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._update(
                job.id, status=ReplayStatus.FAILED, completed_at=datetime.now(UTC),
                failure_message="Replay failed; inspect service logs with the job identifier.",
            )
        finally:
            self._tasks.pop(job.id, None)

    async def _delay(self, seconds: float, job_id: UUID) -> None:
        remaining = max(0.0, seconds)
        while remaining > 0:
            if await self._cancel_requested(job_id):
                return
            step = min(0.25, remaining)
            await asyncio.sleep(step)
            remaining -= step

    async def _cancel_requested(self, job_id: UUID) -> bool:
        job = await self.get(job_id)
        return job is None or job.cancel_requested

    async def _update(self, job_id: UUID, **changes: object) -> ReplayJob | None:
        async with self.session_factory() as session:
            async with session.begin():
                return await ReplayRepository(session).update(job_id, **changes)

    async def _finish(self, job_id: UUID, status: ReplayStatus) -> None:
        updated = await self._update(job_id, status=status, completed_at=datetime.now(UTC))
        if updated is not None:
            await self._broadcast(updated)

    async def _broadcast(self, job: ReplayJob) -> None:
        from nemwatch.api.schemas import ReplayResponse

        await self.hub.broadcast({
            "type": "replay_progress", "data": ReplayResponse.from_domain(job).model_dump(mode="json")
        })
