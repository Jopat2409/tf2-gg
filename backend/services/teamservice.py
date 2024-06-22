"""
All functions related to scraping team and roster data from the three main tf2 APIs:
    - RGL
    - ETF2L (coming soon!)
    - UGC (don't have API so will have to scrape)
"""
from db.team import Team
from db.match import Match

from utils.logger import Logger
from utils.typing import SiteID, TfSource
from utils.scraping import scrape_parallel, TfDataDecoder

# Setup logging
team_logger = Logger.get_logger()

def get_rgl_teams_from_matches(matches: list[Match]) -> list[SiteID]:

    unique_rosters = set()

    for match in matches:
        unique_rosters.add(match.home_team)
        unique_rosters.add(match.away_team)

    return list(unique_rosters)

def scrape_rgl_rosters(team_ids: list[SiteID]) -> list[Team]:
    team_logger.log_info("Scraping roster data")

    rosters_to_scrape = [f"https://api.rgl.gg/v0/teams/{roster.get_id()}" for roster in team_ids]
    teams = []

    scraped = 0
    for results in scrape_parallel(rosters_to_scrape, 9):
        scraped += len(results)
        team_logger.log_info(f"Scraping rosters {(scraped) * 100 / len(rosters_to_scrape):.2f}%, ({scraped}/{len(rosters_to_scrape)})", end='\r')

        if not results:
            team_logger.log_warn(f"No results came back for team IDs {scraped}")

        teams += [TfDataDecoder.decode_team(TfSource.RGL, result) for result in results]

    team_logger.log_info(f"Added {len(teams)} new rosters", start='\n')
    return teams
