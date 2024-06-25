import requests
from typing import Optional

from db.player import Player
from db.team import Team

from utils.scraping import TfDataDecoder, epoch_from_timestamp
from utils.typing import TfSource

def _scrape_player_teams_rgl(steam_id: int) -> list[Team]:

    # Query API
    teams = requests.get(f"https://api.rgl.gg/v0/profile/{steam_id}/teams")

    # Return empty list if failure
    if teams.status_code != 200:
        return []

    # Parse team and add player to the team player list
    def parse_team(team):
        parsed_team = TfDataDecoder.decode_team(TfSource.RGL, team)
        parsed_team.add_player(steam_id, epoch_from_timestamp(team["startedAt"]), epoch_from_timestamp(team["leftAt"]) or None)
        return parsed_team

    # list comp!
    return list(map(parse_team, teams.json()))

def _scrape_player_teams_etf2l(steam_id: int) -> list[Team]:

    # TODO: Fix this method!! I HATE ETF2L API!!!
    return []

    # Query API
    teams = requests.get(f"https://api-v2.etf2l.org/player/{steam_id}")

    # Return empty list if failure
    if teams.status_code != 200:
        return []

    # Parse team and add player
    def parse_team(team):
        parsed_team = TfDataDecoder.decode_team(TfSource.ETF2L, team)
        parsed_team.add_player(steam_id, epoch_from_timestamp(team["startedAt"]), epoch_from_timestamp(team["leftAt"]) or None)
        return parsed_team

    return list(map(parse_team, teams.json()))

def scrape_player_teams(steam_id: int) -> list[Team]:
    teams: list[Team] = _scrape_player_teams_rgl(steam_id) + _scrape_player_teams_etf2l(steam_id)
    return teams

def scrape_player_data(steam_id) -> Optional[Player]:
    """Scrapes the data of a single player. Uses RGL info as a default if player info exists for all platforms

    Args:
        steam_id (_type_): _description_

    Returns:
        Optional[Player]: _description_
    """
    player_data = requests.get(f"https://api.rgl.gg/v0/profile/{steam_id}")
    if player_data.status_code != 200:
        return None
    return TfDataDecoder.decode_player(TfSource.RGL, player_data.json())
