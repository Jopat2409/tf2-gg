from utils.logger import Logger

import os

os.environ["db"] = ":memory:"
import db.database as db

def pytest_sessionstart(session):
    print("skibidi")
    Logger.init("logs", "tests")
    db.regenerate_db()
