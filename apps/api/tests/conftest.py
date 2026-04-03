import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.issuer.auth.models  # noqa: F401
import app.issuer.cards.models  # noqa: F401
import app.ledger.models  # noqa: F401
import app.payments.models  # noqa: F401
from shared.db.base import Base

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/payments_test"
)


@pytest.fixture(scope="function")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def session(engine):
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()
