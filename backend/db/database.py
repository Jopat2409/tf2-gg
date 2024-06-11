import os
import sqlite3
from flask import g, has_app_context
from dotenv import load_dotenv

from app import app

load_dotenv()

DATABASE = f'{os.getenv("ENV", "dev")}.db'

def get_db():
    if has_app_context():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
            db.row_factory = sqlite3.Row
        return db
    else:
        return sqlite3.connect(DATABASE)

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def insert_db(query, args=()):
    cur = get_db().execute(query, args)
    cur.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
