import pytest
from sqlalchemy import text

from nemwatch.config import Settings
from nemwatch.persistence.database import create_engine, create_session_factory


@pytest.fixture
async def db_session():
    settings = Settings()  # type: ignore[call-arg]
    engine = create_engine(settings)
    factory = create_session_factory(engine)
    async with factory() as session:
        yield session
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE alerts, dispatch_observations, replay_jobs RESTART IDENTITY"))
    await engine.dispose()
