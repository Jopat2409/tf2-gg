from flask import Blueprint
from flask import jsonify
from models import Player, MatchResult, RosterPlayerAssociation

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
    player = Player.query.filter(Player.steam_id == player_id).first()
    if not player:
        return jsonify({'success': False, 'data': {}})
    return jsonify({})

@player_api.route("/<player_id>/matches")
def get_player_matches(player_id):
    player = Player.query.filter(Player.steam_id == player_id).first()
    if not player:
        return jsonify({'success': False, 'data': [], 'error': f"Player with player_id {player_id} does not exist"})
    # get rosters with player on
    associations = RosterPlayerAssociation.query.filter(RosterPlayerAssociation.player_id == int(player_id))
    matches = MatchResult.query.filter(MatchResult.team_id.in_([roster.roster_id for roster in associations])).all()
    return jsonify({'success': True, 'data': [match.json() for match in matches]})
