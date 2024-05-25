from models import Team
from database import init_db, db_session
from sqlalchemy import func
import json

def update_unique_teams(team_buffer: dict, team: dict) -> None:
    """
    Takes a dictionary of teams (keyed by the team name) and either
    adds the given team data to the dictionary if the team hasn't been seen before,
    or updates the list of rosters for the team if it has already been saved

    params:
        team_buffer[dict]: buffer to save the teams to
        team[dict]: team data taken straight from the rgl API

    returns:
        None
    """

    # Extract data
    name, tag, roster = team["teamName"], team["teamTag"], team["teamId"]
    unique_team = team_buffer.get(name, None)

    # Add the team if it does not already exist
    if unique_team is None:
        team_buffer.update({name: {
            "team-name": name,
            "display-tag": tag,
            "rosters": []
        }})

    # Add new roster id
    team_buffer[name]["rosters"].append(roster) if roster not in team_buffer[name]["rosters"] else 0

def filter_teams(infile: str, outfile: str, verbose: bool = False) -> None:

    with open(infile, "r") as f:
        matches = json.load(f).get("matches", [])

    from services import read_or_create
    teams = read_or_create(outfile, {})

    num_current_teams = len(teams)

    teams_from_matches = set([team["teamName"] for match in matches for team in matches[match]["teams"]])

    if len(teams_from_matches) == num_current_teams:
        if verbose:
            print("No new teams to scrape")
        return

    for i, match_id in enumerate(matches):
        game = matches[match_id]
        if verbose:
            print(f"Filtering teams {i / len(matches) * 100:.2f}%", end="\r")
        for team in game["teams"]:
            update_unique_teams(team_buffer=teams, team=team)
    # Save to outfile
    with open(outfile, "w") as f:
        json.dump(teams, f)

    if verbose:
        print(f"\nFound {len(teams) - num_current_teams} new teams")

def scrape_rosters(infile: str, outfile: str, verbose: bool = False) -> None:
    print("Scraping roster data")
    with open(infile, "r") as f:
        teams = json.load(f)

    from services import read_or_create
    roster_data = read_or_create(outfile, {})

    rosters = [roster_id for team in teams for roster_id in teams[team]["rosters"]]
    rosters_to_scrape = [f"https://api.rgl.gg/v0/teams/{roster_id}" for roster_id in rosters if str(roster_id) not in roster_data]

    if not rosters_to_scrape:
        if verbose:
            print("No new rosters to scrape")
        return

    from services import scrape_parallel
    for results in scrape_parallel(rosters_to_scrape, 9):
        if verbose:
            print(f"Scraping rosters {len(roster_data.keys()) * 100 / len(rosters):.2f}%", end="\r")
        for result in results:
            roster_data.update({result["teamId"]: result})

    print(f"\nAdded {len(rosters_to_scrape)} new rosters")
    with open(outfile, "w") as f:
        json.dump(roster_data, f)

def insert_team(team_name: str, team_tag: str) -> bool:
    if Team.query.filter(Team.display_name == team_name).first():
        return False
    to_add = Team(team_name, team_tag)
    db_session.add(to_add)
    db_session.commit()
    return True

def insert_teams(infile: str, verbose: bool = False):
    with open(infile, "r") as f:
        in_json = json.load(f)

    teams = in_json.keys()

    if len(teams) == db_session.query(func.count(Team.team_id)).first()[0]:
        if verbose:
            print("No new teams to add to database")
        return

    num_added = 0
    for i, _team in enumerate(teams):
        if verbose:
            print(f"Inserting teams {(i+1)*100 / len(teams):.2f}%", end='\r')
        team_data = in_json[_team]
        num_added += insert_team(team_data['team-name'], team_data['display-tag'])
    if verbose:
        print(f"\nInserted {num_added} new teams to database")

def update(verbose: bool = False):
    # Make sure that all team data is
    init_db()
    filter_teams(infile="data\\rgl_match_data_detailed.json", outfile="data\\rgl_team_data.json", verbose=verbose)
    insert_teams(infile="data\\rgl_team_data.json", verbose=verbose)
    scrape_rosters(infile="data\\rgl_team_data.json", outfile="data\\rgl_roster_data.json", verbose=True)
    db_session.remove()
