from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from nemwatch.persistence.repositories import AlertRepository, DispatchRepository, ReplayRepository


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session


def get_dispatch_repository(session: AsyncSession = Depends(get_session)) -> DispatchRepository:
    return DispatchRepository(session)


def get_alert_repository(session: AsyncSession = Depends(get_session)) -> AlertRepository:
    return AlertRepository(session)


def get_replay_repository(session: AsyncSession = Depends(get_session)) -> ReplayRepository:
    return ReplayRepository(session)
