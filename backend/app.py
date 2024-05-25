from flask import Flask
from database import db_session, init_db
from endpoints.player import player_api

app = Flask(__name__)
app.register_blueprint(player_api, url_prefix='/player')

init_db()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
