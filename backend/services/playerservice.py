from database import db_session
from sqlalchemy import func
from utils.logger import Logger
from utils.file import read_or_create
from utils.scraping import scrape_parallel
from models import Player
import json

__logger = Logger.get_logger()

def scrape_player_data(infile: str, outfile: str, verbose: bool = False):

    with open(infile, "r") as f:
        roster_data = json.load(f)
    __logger.log_info("Scraping player data")

    player_data = read_or_create(outfile, {})

    players = set([player["steamId"] for roster in roster_data for player in roster_data[roster]["players"]])
    urls = [f"https://api.rgl.gg/v0/profile/{_id}" for _id in players if str(_id) not in player_data.keys()]

    if not urls:
        __logger.log_info("No new players to scrape")
        return

    for i, results in enumerate(scrape_parallel(urls, batch_size=9)):
        __logger.log_info(f"Scraping players {len(player_data.keys()) * 100 / len(players):.2f}%", end='\r')
        for result in results:
            player_data.update({result['steamId']: result})

        if i % 10 == 0:
            with open(outfile, "w") as f:
                json.dump(player_data, f)
    __logger.log_info(f"Added {len(urls)} new players to database", start='\n')
    with open(outfile, "w") as f:
        json.dump(player_data, f)


def insert_player(player_data: dict) -> bool:

    if Player.query.filter(Player.steam_id == int(player_data['steamId'])).first():
        return False

    to_add = Player(int(player_data["steamId"]), player_data["name"], bool(player_data["status"]["isBanned"]), bool(player_data["status"]["isVerified"]), player_data["avatar"])
    db_session.add(to_add)
    db_session.commit()
    return True

def insert_players(infile: str, verbose: bool = False) -> None:

    with open(infile, "r") as f:
        players = json.load(f)

    if len(players) == db_session.query(func.count(Player.steam_id)).first()[0]:
        __logger.log_info("No new players to add to database")
        return

    num_added = 0
    for i, player in enumerate(players):
        __logger.log_info(f"Inserting players {i * 100 / len(players):.2f}%", end='\r')
        num_added += insert_player(players[player])

    __logger.log_info(f"Inserted {num_added} new players to database", start='\n')

def update(verbose: bool = False):
    scrape_player_data(infile="data\\rgl_roster_data.json", outfile="data\\rgl_player_data.json", verbose=verbose)
