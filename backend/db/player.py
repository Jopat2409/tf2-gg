from __future__ import annotations
from typing import Optional

import sqlite3

from db.database import update_db, query_db

from utils.logger import Logger
from utils.typing import TfSource

player_logger = Logger.get_logger()

class Player:
    steam_id: int

    alias: str
    avatar: str
    forename: str
    surname: str

    def __init__(self,
                    steam_id: str,
                    alias: Optional[str] = None,
                    avatar: Optional[str] = None,
                    forename: Optional[str] = None,
                    surname: Optional[str] = None):

        self.steam_id = int(steam_id)
        self.alias = alias
        self.avatar = avatar
        self.forename = forename
        self.surname = surname

    def serialize(self) -> dict:
        return {
            "player": {
                "steamId": self.steam_id,
                "displayName": self.alias,
                "avatar": self.avatar,
                "forename": self.forename,
                "surname": self.surname
            }
        }

    def __repr__(self) -> str:
        return f"Player: {self.alias} ({self.steam_id})"

    def __eq__(self, other: Player) -> bool:
        if not isinstance(other, Player):
            return False
        return self.steam_id == other.steam_id and\
                self.alias == other.alias and\
                self.avatar == other.avatar and\
                self.forename == other.forename and\
                self.surname == other.surname

def insert_player(player: Player) -> bool:
    """Inserts a player into the database.

    If the player does not already exist then the player is inserted and the changes committed, otherwise a warning is
    issued to the logger

    Args:
        player (Player): The `Player` object to be inserted into the database

    Returns:
        bool: `True` if the player was successfully inserted, else `False`
    """
    try:
        update_db("INSERT INTO players (steam_id, alias, avatar, forename, surname) VALUES (?, ?, ?, ?, ?)", (player.steam_id, player.alias, player.avatar, player.forename, player.surname,))
    except sqlite3.IntegrityError as _:
        player_logger.log_warn(f"Player {player.steam_id} already exists in database")
        return False
    return True

def insert_players(players: list[Player]) -> bool:
    """Function for bulk-inserting players into the database. Uses bulk queries for checking integrity errors
    and insertion to make it faster for large arrays of players.

    This function is faster than looping and calling `insert_player` manually when the number of players is greater than around 7,
    but the difference for smaller values of n is minimal so it almost always makes sense to just use this method

    Args:
        players (list[Player]): players to insert into the database.

    Returns:
        bool: `False` if all players were already present in the database, else `True`
    """

    # Find which players are not already in the database
    disallowed_players = [p["steam_id"] for p in query_db("SELECT steam_id FROM players WHERE steam_id IN ("+ "?,"*(len(players) - 1) + "?);", tuple(p.steam_id for p in players))]
    allowed_players = [p for p in players if p.steam_id not in disallowed_players]

    # If there is nothing to add then return failure
    if not allowed_players:
        return False

    # Construct the bulk statement and bindings
    stmt = "INSERT INTO players (steam_id, alias, avatar, forename, surname) VALUES " + "(?, ?, ?, ?, ?), "*(len(allowed_players) - 1) + "(?, ?, ?, ?, ?);"
    bindings = ((p.steam_id, p.alias, p.avatar, p.forename, p.surname) for p in allowed_players)
    bindings = tuple(e for tupl in bindings for e in tupl)

    # Run the INSERT query
    update_db(stmt, bindings)

    return True

def get_player(steam_id: int) -> Optional[Player]:
    """Gets a player from the database given the steam64 ID of the player

    Args:
        steam_id (int): The steam64 ID of the player

    Returns:
        Optional[Player]: The `Player` corresponding to the steam_id if it exists, else `None`
    """
    from utils.scraping import TfDataDecoder

    player_data = query_db("SELECT steam_id AS steamId, alias AS displayName, avatar, forename, surname FROM players WHERE steam_id = ?", (steam_id,), one=True)

    if not player_data:
        return None

    return TfDataDecoder.decode_player(TfSource.INTERNAL, {"player": player_data})

def update_player(player: Player) -> bool:
    """Updates the player data in the database with the data of the player passed as a parameter

    Uses `player.steam_id` to determine which player is being updated, and so it will return False if there
    is no player with the same steam_id already in the database

    Args:
        player (Player): The player to update

    Returns:
        bool: Whether the player was successfully updated `True` else `False`
    """

    if not get_player(player.steam_id):
        player_logger.log_warn(f"Attempting to update player {player.steam_id}, when this player does not exist in the database")
        return False

    update_db("UPDATE players SET alias = ?, avatar = ?, forename = ?, surname = ? WHERE steam_id = ?", (player.alias, player.avatar, player.forename, player.surname, player.steam_id))
    return True

def get_teams(steam_id: int) -> list:
    """Gets all teams that the given player has been a part of (from each league RGL ETF2L and UGC)

    Args:
        steam_id (int): The steam64 ID of the player

    Returns:
        list[Team]: List of team objects representing the teams the player has been a part of
    """
    team_data = query_db("SELECT r.rosterId, r.joinedAt, r.leftAt, rosters.team_name AS teamName, rosters.team_tag AS teamTag FROM (SELECT roster_id AS rosterId, joined_at AS joinedAt, left_at AS leftAt FROM roster_player_association WHERE player_id = ?) AS r INNER JOIN rosters ON r.rosterId = rosters.roster_id", (steam_id,))
    return team_data

def get_current_teams(steam_id: int) -> list:
    """Gets all teams that the given player is still currently a part of

    Args:
        steam_id (int): the steam64 ID of the player.

    Returns:
        list: list of team objects representing the current teams.
    """
    return query_db("SELECT r.rosterId, r.joinedAt, r.leftAt, rosters.team_name AS teamName, rosters.team_tag AS teamTag FROM (SELECT roster_id AS rosterId, joined_at AS joinedAt, left_at AS leftAt FROM roster_player_association WHERE player_id = ?) AS r INNER JOIN rosters ON r.rosterId = rosters.roster_id WHERE r.leftAt IS NULL", (steam_id,))

def add_to_team(steam_id: int, team_id: int, joined: float, left: Optional[float] = None) -> bool:
    """Adds the given player to the given team

    Args:
        steam_id (int): the steam64 ID of the player to add.
        team_id (int): the internal team ID of the team to add the player to.
        joined (float): the epoch timestamp of the date the player joined the team.
        left (Optional[float], optional): the epoch timestamp of the date the player left the team (or `None` if the player is still on the team). Defaults to None.

    Returns:
        bool: whether the insert was successful.
    """

    # Add the player-roster record if it doesn't already exist
    try:
        update_db("INSERT INTO roster_player_association (roster_id, player_id, joined_at, left_at) VALUES (?, ?, ?, ?)", (team_id, steam_id, joined, left))
    except sqlite3.IntegrityError:
        player_logger.log_warn(f"Attempting to add duplicate player roster binding ({steam_id}, {team_id}, {joined})")
        return False
    return True
