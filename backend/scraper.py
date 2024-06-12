import sys
import json

from services import MatchService
from utils.logger import Logger
from utils.file import read_or_create
from utils.scraping import TfDataDecoder, TfDataEncoder


def commit_matches_to_file():
    matches = read_or_create("data\\etf2l_matches.json", [])

    PER_PAGE = 20
    start = (len(matches) // PER_PAGE) + 1

    pages = range(start, MatchService.get_last_etf2l_match_page() + 1)
    n = len(pages) // 10

    for pages_ in [pages[i: i + n] for i in range(0, len(pages), n)]:
        matches += MatchService.scrape_etf2l_matches(pages=pages_)
        with open("data\\etf2l_matches.json", "w", encoding='utf-8') as f:
            json.dump(matches, f, cls=TfDataEncoder)

    matches = {match.match_id: match for match in matches}

    with open("data\\etf2l_matches.json", "w", encoding='utf-8') as f:
            json.dump(list(matches.values()), f, cls=TfDataEncoder)

if __name__ == "__main__":
    args = sys.argv[1::]

    Logger.init("logs", "scraper", "verbose" in args)

    __logger = Logger.get_logger()
    commit_matches_to_file()
