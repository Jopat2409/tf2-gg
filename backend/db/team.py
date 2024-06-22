from __future__ import annotations

from utils.typing import SiteID
from typing import Optional

class Team:

    team_id: SiteID
    name: str
    tag: str
    created: float
    updated: float
    players: list[int]
    linked_teams: list[SiteID]

    def __init__(self,
                    team_id: SiteID,
                    name: Optional[str] = None,
                    tag: Optional[str] = None,
                    created: Optional[float] = None,
                    updated: Optional[float] = None,
                    linked_teams: list = [],
                    players: list = []) -> None:
        self.team_id = team_id
        self.name = name
        self.tag = tag
        self.created = created
        self.updated = updated
        self.linked_teams = linked_teams
        self.players = players
    
    def add_player(self, steam_id: int) -> None:
        self.players.append(steam_id)
    
    def add_linked_team(self, team: SiteID) -> None:
        self.linked_teams.append(team)

    def to_dict(self) -> dict:
        return {
            "teamId": self.team_id,
            "teamName": self.name,
            "teamTag": self.tag,
            "createdAt": float(self.created),
            "updatedAt": float(self.updated),
            "players": self.players,
            "linkedTeams": self.linked_teams 
        }
    
    def __eq__(self, other: Team) -> bool:
        if not isinstance(other, Team):
            return False
        return self.team_id == other.team_id and\
                self.name == other.name and\
                self.created == other.created and\
                self.updated == other.updated and\
                all([player in other.players for player in self.players]) and\
                all([team in other.linked_teams for team in self.linked_teams])