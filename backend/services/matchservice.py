from utils.logger import Logger
from utils.scraping import post_request, scrape_parallel
from utils.typing import SiteID, TfSource

from models import Match, MatchResult
from database import db_session

match_logger = Logger.get_logger()

def scrape_rgl_match_page(start: int, take: int = 1000) -> list:
    """
    Scrape a single match page from RGL and return the match IDs found

    params:
        start[int]: how many matches to skip
        take[int]: how many matches to take (max 1000)

    returns:
        ids[list]: list of unique match IDs
    """
    _, response = post_request("https://api.rgl.gg/v0/matches/paged", default=[], take=str(take), skip=str(start))

    return [SiteID(data["matchId"], TfSource.RGL) for data in response]

def scrape_rgl_match_ids() -> int:
    match_logger.log_info("Scraping rgl match IDs")

    num_stored = Match.get_count(TfSource.RGL)
    next_match_data = scrape_rgl_match_page(num_stored)

    if not next_match_data:
        match_logger.log_info("No new matches found")
        return 0

    while next_match_data:
        for _id in next_match_data:
            match_logger.log_info(f"Inserting match with ID {_id.get_id()}", end='\r')
            Match.insert(db_session, _id, commit=False)
        db_session.commit()
        next_match_data = scrape_rgl_match_page(Match.get_count(TfSource.RGL))

    match_logger.log_info(f"Added {Match.get_count(TfSource.RGL) - num_stored} new matches to the database")


def insert_rgl_match(match: dict) -> bool:

    if Match.get_rgl_match(int(match["matchId"])).is_complete:
        return False

    from services import TeamService

    home_team, away_team = match["teams"]
    home_team_id = TeamService.insert_roster_id(home_team["teamId"])
    away_team_id = TeamService.insert_roster_id(away_team["teamId"])

    m = Match.get_rgl_match(int(match["matchId"]))
    m.update_from_rgl_data(match)

    for _map in match["maps"]:
        homeResult = MatchResult(int(match["matchId"]), int(home_team_id), _map["mapName"], _map["homeScore"] if _map["homeScore"] is not None else -1)
        awayResult = MatchResult(int(match["matchId"]), int(away_team_id), _map["mapName"], _map["awayScore"] if _map["homeScore"] is not None else -1)

        db_session.add_all([homeResult, awayResult])
    m.is_complete = True
    db_session.commit()

def scrape_detailed_rgl_matches() -> int:

    match_logger.log_info("Scraping match details from RGL website")

    match_ids = [match.rgl_match_id for match in Match.get_incomplete("RGL")]

    if not match_ids:
        match_logger.log_info("No additional matches to scrape")
        return

    to_scrape = [f"https://api.rgl.gg/v0/matches/{_id}" for _id in match_ids]
    num_added = 0

    for result in scrape_parallel(to_scrape, 9):
        num_added += len(result)
        match_logger.log_info(f"Scraping detailed matches {(num_added*100) / len(to_scrape):.2f}%, ({num_added} / {len(to_scrape)})", end='\r')
        for r in result:
            insert_rgl_match(r)

    match_logger.log_info(f"Added {num_added} new detailed match data", start='\n')

def update() -> None:
    scrape_rgl_match_ids()
    scrape_detailed_rgl_matches()
