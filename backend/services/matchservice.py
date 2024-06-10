from utils.logger import Logger
from utils.scraping import post_request, scrape_parallel
from utils.typing import SiteID, TfSource, TfDataDecoder

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
    """
    Scrapes a set containing the IDs of all RGL matches played since its inception.
    """
    match_logger.log_info("Scraping rgl match IDs")

    # Get the data from after the last match stored in the database
    num_stored = Match.get_count(TfSource.RGL)
    next_match_data = scrape_rgl_match_page(num_stored)

    # If no data returned then we are up to date
    if not next_match_data:
        match_logger.log_info("No new matches found")
        return 0

    # While we are getting data from the endpoint, add it to the database
    while next_match_data:
        for _id in next_match_data:
            match_logger.log_info(f"Inserting match with ID {_id.get_id()}", end='\r')
            Match.insert(db_session, _id, commit=False)
        db_session.commit()
        # Offset request by number of matches in database
        next_match_data = scrape_rgl_match_page(Match.get_count(TfSource.RGL))

    match_logger.log_info(f"Added {Match.get_count(TfSource.RGL) - num_stored} new matches to the database")

def scrape_rgl_matches(rgl_ids: list[int]):
    match_logger.log_info("Scraping match details from RGL website")
    to_scrape = [f"https://api.rgl.gg/v0/matches/{_id}" for _id in rgl_ids]
    num_added = 0

    for result in scrape_parallel(to_scrape, 9):
        num_added += len(result)
        match_logger.log_info(f"Scraping detailed matches {(num_added*100) / len(to_scrape):.2f}%, ({num_added} / {len(to_scrape)})", end='\r')
        for match_data in result:
            new_match = TfDataDecoder.decode_match(TfSource.RGL, match_data)
            Match.update(new_match, commit=False)
        db_session.commit()

    match_logger.log_info(f"Added {num_added} new detailed match data", start='\n')


def scrape_rgl() -> int:

    scrape_rgl_match_ids()
    match_ids = [match.rgl_match_id for match in Match.get_incomplete(TfSource.RGL)]

    if not match_ids:
        match_logger.log_info("No additional matches to scrape")
        return

    scrape_rgl_match_ids(match_ids)

def scrape_etf2l_matches() -> int:
    pass

def scrape_etf2l():
    pass

def scrape_ugc():
    pass
