import os
import sqlite3
from flask import g, has_app_context
from dotenv import load_dotenv

from utils.logger import Logger
from utils.file import read_required

load_dotenv()
database_logger = Logger.get_logger()

DATABASE = os.getenv("db", "dev.db")
db_handle: sqlite3.Connection = None
database_logger.log_info(f"Initialised database {DATABASE}")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    if has_app_context():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
            db.row_factory = dict_factory
        return db
    else:
        global db_handle
        if db_handle is None:
            db_handle = sqlite3.connect(DATABASE)
            db_handle.row_factory = dict_factory
        return db_handle

# @database_logger.describe("Query Database: ")
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# @database_logger.describe("Update Database: ")
def update_db(query, args=()):
    cur = get_db().execute(query, args)
    get_db().commit()
    cur.close()

def regenerate_db():
    database_logger.log_info(f"Regenerating database for {DATABASE}")
    schema = read_required("db\\db.schema")
    get_db().executescript(schema)
