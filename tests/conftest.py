import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base, get_db
from app.main import app
from app.settings import settings


@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.database.test_database_connection_string)


@pytest.fixture(scope="session", autouse=True)
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autoflush=False, bind=connection)()
    app.dependency_overrides[get_db] = lambda: session
    yield session

    session.close()
    transaction.rollback()
    connection.close()

