from database import init_db, db_session
import json

def scrape_player_data(infile: str, outfile: str, verbose: bool = False):

    with open(infile, "r") as f:
        roster_data = json.load(f)
    print("Scraping player data")
    from services import read_or_create
    player_data = read_or_create(outfile, {})

    players = set([player["steamId"] for roster in roster_data for player in roster_data[roster]["players"]])
    urls = [f"https://api.rgl.gg/v0/profile/{_id}" for _id in players if str(_id) not in player_data.keys()]

    if not urls:
        if verbose:
            print("No players to add")
        return

    from services import scrape_parallel
    for i, results in enumerate(scrape_parallel(urls, batch_size=9)):
        if verbose:
            print(f"Scraping players {len(player_data.keys()) * 100 / len(players):.2f}%", end='\r')
        for result in results:
            player_data.update({result['steamId']: result})

        if i % 10 == 0:
            with open(outfile, "w") as f:
                json.dump(player_data, f)
    print(f"\nAdded {len(urls)} new players to database")
    with open(outfile, "w") as f:
        json.dump(player_data, f)


def update(verbose: bool = False):
    init_db()
    scrape_player_data(infile="data\\rgl_roster_data.json", outfile="data\\rgl_player_data.json", verbose=verbose)
    db_session.remove()
