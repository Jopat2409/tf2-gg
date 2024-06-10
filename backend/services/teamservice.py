from models import Roster, Player, RosterPlayerAssociation
from utils.scraping import scrape_parallel
from utils import epoch_from_timestamp
from database import db_session
from utils import Logger

team_logger = Logger.get_logger()


def insert_roster(roster_data: dict) -> None:

    roster = Roster.get_rgl_roster(int(roster_data["teamId"]))
    roster.update_from_rgl_data(roster_data)

    for player in roster_data["players"]:
        p = Player.query.filter(Player.steam_id == int(player["steamId"])).first()
        if not p:
            p = Player()
            p.steam_id = int(player["steamId"])
            db_session.add(p)
            db_session.commit()
        if not RosterPlayerAssociation.query.filter(RosterPlayerAssociation.player_id == int(player["steamId"]),
                                                    RosterPlayerAssociation.roster_id == roster.roster_id,
                                                    RosterPlayerAssociation.joined_at == epoch_from_timestamp(player["joinedAt"])):
            ass = RosterPlayerAssociation(p, roster, epoch_from_timestamp(player["joinedAt"]), epoch_from_timestamp(player["leftAt"]))
            db_session.add(ass)

    roster.is_complete = True
    db_session.commit()

def scrape_rgl_rosters() -> int:
    team_logger.log_info("Scraping roster data")

    rosters_to_scrape = [f"https://api.rgl.gg/v0/teams/{roster.rgl_team_id}" for roster in Roster.get_incomplete()]

    scraped = 0
    for results in scrape_parallel(rosters_to_scrape, 9):
        scraped += len(results)
        team_logger.log_info(f"Scraping rosters {(scraped) * 100 / len(rosters_to_scrape):.2f}%, ({scraped}/{len(rosters_to_scrape)})", end='\r')

        if not results:
            team_logger.log_warn(f"No results came back for team IDs {scraped}")

        for result in results:
            insert_roster(result)

    team_logger.log_info(f"Added {len(rosters_to_scrape)} new rosters", start='\n')

def update():
    # Make sure that all team data is
    scrape_rgl_rosters()
