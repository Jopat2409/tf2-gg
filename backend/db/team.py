from __future__ import annotations
from typing import Optional

import sqlite3

from db.database import query_db, update_db

from utils.typing import SiteID, TfSource
from utils.logger import Logger

team_logger = Logger.get_logger()

class Team:

    team_id: SiteID
    name: str
    tag: str
    created: float
    updated: float
    players: dict
    linked_teams: list[SiteID]

    def __init__(self,
                    team_id: SiteID,
                    name: Optional[str] = None,
                    tag: Optional[str] = None,
                    created: Optional[float] = None,
                    updated: Optional[float] = None,
                    linked_teams: list = [],
                    players: list = []) -> None:

        if not isinstance(team_id, SiteID):
            raise ValueError("team_id must be of type SiteID. It cannot be a raw integer")

        self.team_id = team_id
        self.name = name
        self.tag = tag
        self.created = float(created or 0) or None
        self.updated = float(updated or 0) or None
        self.linked_teams = linked_teams
        self.players = players

    def add_player(self, steam_id: int, joined: float, left: Optional[float] = None) -> None:
        self.players.append({"steamId": steam_id, "joinedAt": float(joined), "leftAt": float(left or 0) or None})

    def add_linked_team(self, team: SiteID) -> None:
        self.linked_teams.append(team)

    def serialize(self) -> dict:
        return {"team": {
            "teamId": self.team_id,
            "teamName": self.name,
            "teamTag": self.tag,
            "createdAt": self.created,
            "updatedAt": self.updated,
            "players": self.players,
            "linkedTeams": self.linked_teams
            }
        }

    def __repr__(self) -> str:
        return f"""Team: {self.team_id}, Name: {self.name}, Tag: {self.tag}, players: {self.players}"""

    def __eq__(self, other: Team) -> bool:
        if not isinstance(other, Team):
            return False
        return self.team_id == other.team_id and\
                self.name == other.name and\
                self.created == other.created and\
                self.updated == other.updated and\
                all([player in other.players for player in self.players]) and\
                all([team in other.linked_teams for team in self.linked_teams])

def get_roster_id(source_id: SiteID) -> int:
    return query_db("SELECT roster_id FROM rosters WHERE source_id = ? AND source = ?", (source_id.get_id(), source_id.get_source()), one=True)["roster_id"]

def get_team(team_id: int | SiteID) -> Optional[Team]:
    """Gets a team from the database with the given team ID, or `None` if the team doesn't exist

    Args:
        team_id (int): the internal team ID of the

    Returns:
        Optional[Team]: The `Team` data from the database, or `None` if there is no team corresponding to the team_id given
    """
    stmt = "SELECT roster_id AS rosterId, team_name as teamName, team_tag as teamTag, created_at as createdAt, updated_at AS lastUpdated, source AS dataSource, source_id AS dataId FROM rosters WHERE "
    if isinstance(team_id, int):
        team_data = query_db(stmt + "roster_id = ?", (team_id,), one=True)
    elif isinstance(team_id, SiteID):
        team_logger.log_info("did trhis")
        team_data = query_db(stmt + "source_id = ? AND source = ?", (team_id.get_id(), team_id.get_source(),), one=True)
    else:
        return None

    if not team_data:
        return None

    team = Team(SiteID(team_data["dataId"], TfSource(team_data["dataSource"])), team_data["teamName"], team_data["teamTag"], team_data["createdAt"], team_data["lastUpdated"])
    team.players = query_db("SELECT player_id AS steamId, joined_at AS joinedAt, left_at AS leftAt FROM roster_player_association WHERE roster_id = ?", (team_data["rosterId"],))

    return team

def insert_team(team: Team) -> bool:
    """Inserts a team into the database if the corresponding team source ID does not exist already in the database

    Also inserts all players that are in the team to the database (if they are not already present), and creates an association
    in the database between the team and the player

    Args:
        team (Team): The team to insert into the database

    Returns:
        bool: `True` if the team was successfully inserted, otherwise `False`
    """
    from db.player import add_to_team, insert_player, Player

    try:
        update_db("INSERT INTO rosters (source, source_id, team_name, team_tag, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", (team.team_id.get_source(), team.team_id.get_id(), team.name, team.tag, team.created, team.updated,))
    except sqlite3.IntegrityError as _:
        team_logger.log_warn(f"Team {team.team_id} already exists in database")
        return False

    for player in team.players:
        # Ensure the player is in the database and add it to the team
        insert_player(Player(player["steamId"]))
        add_to_team(player["steamId"], get_roster_id(team.team_id), player["joinedAt"], player["leftAt"])

    return True

def insert_teams(teams: list[Team]) -> bool:
    """Bulk inserts teams into the database

    Bulk inserts all players from all the teams, and bulk adds association records. This method is about 2 orders of magnitude
    faster than just manually looping and inserting so just use this whenever you could possibly be inserting more than one team

    Args:
        teams (list[Team]): list of teams to insert into the database.

    Returns:
        bool: `False` if none of the teams are added into the database, else `True`
    """
    from db.player import insert_players, Player, add_to_team

    # Ensure all players are in the database
    insert_players([Player(p["steamId"]) for team in teams for p in team.players])

    disallowed_teams = query_db("SELECT source_id, source FROM rosters WHERE source_id IN ("+ "?,"*(len(teams) - 1) + "?);", (*tuple(t.team_id.get_id() for t in teams),))
    allowed_teams = [t for t in teams if {"source": t.team_id.get_source(), "source_id": t.team_id.get_id()} not in disallowed_teams]

    if not allowed_teams:
        return False

    # Construct bulk query
    stmt = "INSERT INTO rosters (source, source_id, team_name, team_tag, created_at, updated_at) VALUES " + "(?, ?, ?, ?, ?, ?), "*(len(allowed_teams) - 1) + "(?, ?, ?, ?, ?, ?);"

    # Flatten binding values
    bindings = ((t.team_id.get_source(), t.team_id.get_id(), t.name, t.tag, t.created, t.updated) for t in allowed_teams)
    bindings = tuple(e for tupl in bindings for e in tupl)
    update_db(stmt, bindings)

    # TODO: Figure out how to bulk this up :3
    for team_id, player in [(team.team_id, player) for team in teams for player in team.players]:
        add_to_team(player["steamId"], get_roster_id(team_id), player["joinedAt"], player["leftAt"])

    return True

def update_team(team: Team) -> bool:
    """Updates the given team

    Args:
        team (Team): _description_

    Returns:
        bool: _description_
    """

    if not get_team(team.team_id):
        return False

    from db.player import add_to_team
    team_id = get_roster_id(team.team_id)
    update_db("UPDATE rosters SET team_name = ?, team_tag = ?, created_at = ?, updated_at = ? WHERE roster_id = ?", (team.name, team.tag, team.created, team.updated, team_id,))

    for player in team.players:
        print(player)
        add_to_team(player["steamId"], team_id, player["joinedAt"], player["leftAt"])

    return True

def player_in_team(team_id: int, player_id: int, joined: float) -> bool:
    return query_db("SELECT * FROM roster_player_association WHERE roster_id = ? AND player_id = ? AND joined_at = ?", (team_id, player_id, joined), one=True) is not None

