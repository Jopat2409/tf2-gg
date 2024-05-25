import requests
import json
from database import init_db, db_session


def scrape_match_page(start: int) -> dict:
    params = {'take': '1000', 'skip': f'{start}',}
    headers = {'accept': '*/*',}
    response = requests.post("https://api.rgl.gg/v0/matches/paged", params=params, headers=headers, json={})
    return response.json() if response.status_code == 200 else []

def find_match_ids(outfile: str, verbose: bool = False) -> None:

    from services import read_or_create
    match_data_sparse = read_or_create(outfile, [])
    num_matches = len(match_data_sparse)

    finished = False
    while not finished:
        start_no = int((len(match_data_sparse) // 1e3) * 1e3)

        next_match_data = scrape_match_page(start_no)
        ids = [match["matchId"] for match in next_match_data]
        if str(ids[-1]) == str(match_data_sparse[-1]):
            if verbose:
                print("No new matches to find")
            return
        if ids != []:
            if verbose:
                print(f"Scraping matches {start_no} - {start_no + 1e3}", end='\r')
            match_data_sparse += ids
        else:
            finished = True

    unique_matches = list(set(match_data_sparse))

    with open(outfile, "w") as f:
        json.dump(unique_matches, f)

    if verbose:
        print(f"\nFound {len(unique_matches) - num_matches} new matches")

def scrape_detailed_matches(infile: str, outfile: str, verbose: bool = False) -> None:
    with open(infile, "r") as f:
        match_ids = json.load(f)

    from services import read_or_create
    detailed_matches = read_or_create(outfile, {"matches": {}})
    scraped_matches = detailed_matches["matches"].keys()

    to_scrape = [f"https://api.rgl.gg/v0/matches/{_id}" for _id in match_ids if str(_id) not in scraped_matches]

    if not to_scrape:
        if verbose:
            print("No additional matches to scrape")
        return

    from services import scrape_parallel
    for i, result in enumerate(scrape_parallel(to_scrape, 9)):
        if verbose:
            print(f"Scraping detailed matches {(len(detailed_matches['matches'].keys())*100) / len(to_scrape):.2f}%", end='\r')
        for r in result:
            detailed_matches["matches"].update({r['matchId']: r})

        if i % 10 == 0:
            with open(outfile, "w") as f:
                json.dump(detailed_matches, f)

    print(f"Added {to_scrape} new detailed match data")
    with open(outfile, "w") as f:
        json.dump(detailed_matches, f)

def update(verbose: bool = False) -> None:
    init_db()
    find_match_ids(outfile="data\\rgl_match_data.json", verbose=verbose)
    scrape_detailed_matches(infile="data\\rgl_match_data.json", outfile="data\\rgl_match_data_detailed.json", verbose=verbose)
    db_session.remove()
