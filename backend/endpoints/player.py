from flask import Blueprint, jsonify, request

from services import PlayerService, TeamService

player_api = Blueprint("player", __name__)

@player_api.route("/<player_id>")
def get_player_(player_id):
    """
    """
    from db.player import insert_player, get_player, get_current_teams, update_player
    from db.team import insert_team


    player = get_player(player_id)
    force_update = request.args.get("force_update", False)

    # If player does not exist, scrape it
    if not player:
        player = PlayerService.scrape_player_data(player_id)
        if player:
            insert_player(player)
        teams = PlayerService.scrape_player_teams(player_id)
        for team in teams:
            insert_team(team)
    # If player has not been scraped or the request forces update from source
    elif player["alias"] is None or force_update:
        player = PlayerService.scrape_player_data(player_id)
        update_player(player)

    # If the player has no registered teams then scrape the player teams
    if not get_current_teams(player_id) or force_update:
        teams = PlayerService.scrape_player_teams(player_id)
        for team in teams:
            insert_team(team)

    player = get_player(player_id)
    player["currentTeam"] = get_current_teams(player_id)

    return jsonify({'success': True, 'data': player})

@player_api.route("/<player_id>/matches")
def get_player_matches(player_id):
    from db.database import query_db
    #TODO: optimise this query!
    matches = query_db("""
                        SELECT filtered_matches.match_id AS matchId, filtered_matches.match_name AS matchName, match_results.map_name AS mapName, match_results.roster_id AS rosterId, match_results.score AS score
                        FROM (SELECT * FROM matches WHERE match_id IN (SELECT match_id FROM match_results WHERE roster_id IN (SELECT roster_id FROM roster_association_table WHERE player_id = ?))) as filtered_matches
                        LEFT JOIN match_results
                            ON filtered_matches.match_id = match_results.match_id
                        """, player_id)

    if not matches:
        return jsonify({'success': False, 'data': []})

    # aggregate functions

    parsed_matches = {}
    for m_ in matches:
        m_["results"] = {}
        if m_["matchId"] not in parsed_matches:
            parsed_matches[m_["matchId"]] = m_
        match = parsed_matches[m_["matchId"]]
        if m_["mapName"] not in match["results"]:
            match["results"][m_["mapName"]] = {m_["rosterId"]: m_["score"]}
        else:
            match["results"][m_["mapName"]].update({m_["rosterId"]: m_["score"]})

    return jsonify({'success': True, 'data': parsed_matches})

@player_api.route('/<player_id>/teams')
def get_player_teams(player_id):
    from db.player import get_teams
    print(player_id)
    return jsonify({'success': True, 'data': get_teams(player_id)})
