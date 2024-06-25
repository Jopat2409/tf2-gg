import sys

from flask import Flask, g
from endpoints.player import player_api
from endpoints.team import team_api

from utils.logger import Logger

from db.database import regenerate_db

app = Flask(__name__)
app.register_blueprint(player_api, url_prefix='/player')
app.register_blueprint(team_api, url_prefix='/team')

Logger.init("logs", "flaskapp", True)

args = sys.argv[1::]
if "create_db" in args:
    regenerate_db()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
