from flask import Blueprint, jsonify, request

from services import TeamService

from utils.typing import SiteID, TfSource

team_api = Blueprint("roster", __name__)

@team_api.route("/<team_id>")
def roster_id(team_id):
    from db.team import get_team, update_team

    # If the team does not exist then return error
    team = get_team(team_id)
    if not team:
        return jsonify({'success': False, 'data': {}})

    # If the team has been partially scraped then update the team's data
    if team["lastUpdated"] is None or request.args.get("force_update", False):
        new_team = TeamService.scrape_team(SiteID(team["dataId"], TfSource(team["dataSource"])))
        update_team(new_team)

    return jsonify({'success': True, 'data': get_team(team_id)})

@team_api.route("/<team_id>/matches")
def roster_matches(team_id):
    from db.team import get_team, update_team
