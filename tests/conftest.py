import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.settings import settings

@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(settings.database.test_database_connection_string)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def setup_test_db(test_db_engine):
    Base.metadata.create_all(bind=test_db_engine)
    yield
    Base.metadata.drop_all(bind=test_db_engine)

@pytest.fixture
def db_session(test_db_engine, setup_test_db):
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(autouse=True)
def clean_tables(db_session):
    """Clean all tables after each test"""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()