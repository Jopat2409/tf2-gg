import sys
import json

from services import MatchService

from db.match import Match

from utils.logger import Logger
from utils.file import read_or_create, write_to_file
from utils.typing import SiteID, TfSource
from utils.scraping import TfDataDecoder, TfDataEncoder

def __scrape_remaining_etf2l_matches(current_matches: dict[TfSource, list[Match]], batches: int = 10) -> None:

    # Calculate the starting page, the number of pages to scrape and the batch size to use (n)
    start = (len(current_matches.get(TfSource.ETF2L, [])) // 20) + 1
    pages = range(start, MatchService.get_last_etf2l_match_page() + 1)
    n = len(pages) // batches

    write: callable = lambda x: write_to_file("data\\match_data.json", x, create=False, json=True, cls=TfDataEncoder)

    # Scrape the remaining mathes in batches and store to the file intermittendly
    for pages_ in [pages[i: i + n] for i in range(0, len(pages), n)]:
        current_matches[TfSource.ETF2L] += MatchService.scrape_etf2l_matches(pages=pages_)
        write([match for matches in current_matches.values() for match in matches])
    
    # Finally, write all matches back to the file
    write([match for matches in current_matches.values() for match in matches])

def __scrape_remaining_rgl_matches(current_matches: dict[TfSource, list[Match]]) -> None:
    pass

def commit_matches_to_file():
    matches: list[SiteID] = read_or_create("data\\match_data.json", default=[], cls=TfDataDecoder)

    separated_matches = {
         source: [match for match in matches if match.get_source() == source] for source in TfSource
    }

    __scrape_remaining_etf2l_matches(separated_matches)
    __scrape_remaining_rgl_matches(separated_matches)

def commit_teams_to_file():
     teams = read_or_create("data\\")

if __name__ == "__main__":
    args = sys.argv[1::]

    Logger.init("logs", "scraper", "verbose" in args)

    __logger = Logger.get_logger()
    commit_matches_to_file()
