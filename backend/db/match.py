from __future__ import annotations
from typing import Optional
from utils.typing import SiteID

class Map:
    map_name: str
    was_played: bool
    home_score: int
    away_score: int

    def __init__(self,
                    name: str,
                    played: bool,
                    home_score: int,
                    away_score: int):
        self.map_name = name
        self.was_played = played
        self.home_score = int(home_score)
        self.away_score = int(away_score)

    def serialize(self) -> dict:
        return {
            "map": {
                "mapName": self.map_name,
                "wasPlayed": self.was_played,
                "homeScore": self.home_score,
                "awayScore": self.away_score
            }
        }

    def __repr__(self) -> str:
        return f"Map: {self.map_name}" + (f" Home: {self.home_score} | Away: {self.away_score}" if self.was_played else "")

    def __eq__(self, other: Map) -> bool:
        if not isinstance(other, Map):
            return False
        return self.map_name == other.map_name and\
                self.was_played == other.was_played and\
                self.home_score == other.home_score and\
                self.away_score == other.away_score

class Match:

    match_id: SiteID
    name: str
    epoch: float
    event_id: SiteID
    was_forfeit: int

    home_team: SiteID
    away_team: SiteID

    maps: list[Map]

    def __init__(self,
                    id_: SiteID,
                    name: Optional[str] = None,
                    epoch: Optional[float] = None,
                    forfeit: Optional[bool] = None,
                    event: Optional[SiteID] = None,
                    home_team: Optional[SiteID] = None,
                    away_team: Optional[SiteID] = None) -> None:
        self.match_id = id_
        self.name = name
        self.epoch = epoch
        self.event_id = event
        self.was_forfeit = forfeit
        self.home_team = home_team
        self.away_team = away_team
        self.maps = []

    def add_map(self, map_: Map) -> None:
        self.maps.append(map_)

    def add_map_data(self, name: str, played: bool, home_score: int = 0, away_score: int = 0) -> None:
        self.maps.append(Map(name, played, home_score, away_score))

    def serialize(self) -> dict:
        return {
            "match": {
                "matchId": self.match_id,
                "matchName": self.name,
                "matchTime": self.epoch,
                "wasForfeit": self.was_forfeit,
                "event": self.event_id,
                "homeTeam": self.home_team,
                "awayTeam": self.away_team,
                "maps": self.maps
                }
            }

    def __repr__(self) -> str:
        return f"Match: {self.match_id}, Name: {self.name}, Time: {self.epoch}, Maps: {self.maps}"

    def __eq__(self, other: Match):
        if not isinstance(other, Match):
            return False
        return self.match_id == other.match_id and\
                self.name == other.name and\
                self.epoch == other.epoch and\
                self.was_forfeit == other.was_forfeit and\
                self.event_id == other.event_id and\
                self.home_team == other.home_team and\
                self.away_team == other.away_team and\
                self.maps == other.maps

