import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.settings import settings


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_async_engine(settings.database.test_database_connection_string)
    yield engine
    engine.sync_engine.dispose()


@pytest.fixture(scope="session")
async def setup_test_db(test_db_engine):
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db_engine, setup_test_db):
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()