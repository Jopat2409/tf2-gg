import os

from sqlalchemy.orm import scoped_session, sessionmaker
from utils.logger import Logger


import pytest

os.environ["db"] = ":memory:"
from database import engine, init_db, teardown_db

def pytest_sessionstart(session):
    Logger.init("logs", "tests", True)

@pytest.fixture(scope='session')
def engine_():
    return engine

@pytest.fixture(scope='session')
def tables(engine_):
    init_db()
    yield
    teardown_db()

@pytest.fixture(scope='function')
def session(engine_, tables):

    conn = engine_.connect()
    transaction = conn.begin()

    Session = scoped_session(sessionmaker(bind=conn))
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    conn.close()
    Session.remove()
