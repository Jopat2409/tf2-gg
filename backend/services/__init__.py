import services.teamservice as TeamService
import services.matchservice as MatchService
import services.playerservice as PlayerService
from database import init_db, db_session

__all__ = [TeamService, MatchService, PlayerService]


def scrape_all_services() -> None:
    """
    Updates all database tables from scraped data, may take a bit of time
    """
    MatchService.update()
    TeamService.update()
    PlayerService.update(True)

def insert_all_services() -> None:
    init_db()
    TeamService.insert_teams(infile="data\\rgl_team_data.json", verbose=True)
    PlayerService.insert_players(infile="data\\rgl_player_data.json", verbose=True)
    TeamService.insert_rosters(infile="data\\rgl_roster_data.json", verbose=True)
    db_session.remove()

def test_func() -> None:
    init_db()
    MatchService.update()
    TeamService.update()
    db_session.remove()
