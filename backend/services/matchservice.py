"""
All functions related to scraping match data from each of the three tf2 APIs:
   - RGL
   - ETF2L
   - UGC (coming soon!)
"""
import time
import requests

from db.match import Match

from utils.logger import Logger
from utils.typing import SiteID, TfSource
from utils.scraping import post_request, scrape_parallel, TfDataDecoder

# Setup logging
match_logger = Logger.get_logger()

def scrape_rgl_match_page(start: int, take: int = 1000) -> list[SiteID]:
    """
    Scrape a single match page from RGL and return the match IDs found

    params:
        start[int]: how many matches to skip
        take[int]: how many matches to take (max 1000)

    returns:
        ids[list]: list of unique match IDs
    """
    _, response = post_request("https://api.rgl.gg/v0/matches/paged", default=[], take=str(take), skip=str(start))

    return [SiteID.rgl_id(data["matchId"]) for data in response]

def scrape_rgl_match_ids(from_: int) -> list[SiteID]:
    """
    Scrapes a set containing the IDs of all RGL matches played since its inception.

    params:
        from_[int]: How many matches to skip
    
    returns:
        matchIds[list]: List containing the ```SiteID``` of each match found
    """
    match_logger.log_info(f"Scraping rgl match IDs, skipped {from_}")

    # Get the data from after the last match stored in the database
    next_match_data = scrape_rgl_match_page(from_, take=1)

    # If no data returned then we are up to date
    if not next_match_data:
        match_logger.log_info("No new matches found")
        return []

    new_ids = []

    # While we are getting data from the endpoint, add it to the database
    while next_match_data:
        match_logger.log_info(f"Found matches up to ID {next_match_data[-1].get_id()}", end='\r')
        new_ids += next_match_data
        # Offset request by number of matches in database
        next_match_data = scrape_rgl_match_page(from_ + len(new_ids))

    match_logger.log_info(f"Found {len(new_ids)} new matches", start='\n')
    return new_ids

def scrape_rgl_matches(rgl_ids: list[int]) -> list[Match]:
    """
    Given a list of RGL match IDs, scrapes the match page for each one and returns a list containing the data for each 
    ID

    params:
        rgl_ids[list]: List containing all the RGL ID's to scrape. Note that all these ids MUST exist
    
    returns:
        matches[list]: List of ```Match``` objects containing the data for all the IDs requested
    """
    match_logger.log_info("Scraping match details from RGL website")
    to_scrape = [f"https://api.rgl.gg/v0/matches/{_id}" for _id in rgl_ids]


    num_scraped = 0
    matches: list[Match] = []

    for results in scrape_parallel(to_scrape, 9):
        num_scraped += len(results)
        match_logger.log_info(f"Scraping RGL matches {(num_scraped*100) / len(to_scrape):.2f}%, ({num_scraped} / {len(to_scrape)})", end='\r')
        matches += [TfDataDecoder.decode_match(TfSource.RGL, match) for match in results]

    match_logger.log_info(f"Scraped {num_scraped} RGL matches", start='\n')

    return matches

def get_last_etf2l_match_page() -> int:
    """
    Gets the value of the final page of matches for the ETF2L API

    returns:
        page[int]: The page number of the last match page that contains matches
    """
    return int(requests.get("https://api-v2.etf2l.org/matches?page=1").json()["results"]["last_page"])

def scrape_etf2l_matches(pages: list[int]):
    """
    Scrape all ETF2L match pages from the given list of page numbers

    params:
        pages[list]: List of page numbers to scrape

    returns:
        list[Match]: List of matches scraped from the given `pages`
    """
    match_logger.log_info("Scraping ETF2L matches")
    
    # Get matches to scrape
    to_scrape = [f"https://api-v2.etf2l.org/matches?page={page}" for page in pages]
    num_scraped = 0
    matches: list[Match] = []

    for results in scrape_parallel(to_scrape, 9, delay_step=1, delay_size=1):
        
        # If no results are returned then we must be rate limited
        if len(results) == 0:
            match_logger.log_warn("Rate limited, sleeping 10 seconds", start="\n")
            time.sleep(10)
        
        # Update matches with results
        num_scraped += len(results)
        match_logger.log_info(f"Scraping detailed matches {(num_scraped*100) / len(to_scrape):.2f}%, ({num_scraped} / {len(to_scrape)})", end='\r')
        matches += [TfDataDecoder.decode_match(TfSource.ETF2L, match) for page in results for match in page["results"]["data"]]

    return matches

