from flask import Blueprint
from flask import jsonify
from models import Player

player_api = Blueprint("player", __name__)

@player_api.route("/<player_id>")
def get_player(player_id):
    """
    Should return
    {
        success: True
        data: {
            display-name: <name>,
            display-tag: <tag>,
            current-team: <team_id>,
            matches: [
                <match_id>
            ]
        }
    }
    """
    player = Player.query.filter(Player.player_id == player_id).first()
    if not player:
        return jsonify({'success': False, 'data': {}})
    return jsonify({})

@player_api.route("/<player_id>/matches")
def get_player_matches(player_id):
    player = Player.query.filteR(Player.player_id == player_id).first()
    if not player:
        return jsonify({'success': False, 'data': [], 'error': f"Player with player_id {player_id} does not exist"})
