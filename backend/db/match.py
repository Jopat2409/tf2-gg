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

    def to_dict(self) -> dict:
        return {
            "mapName": self.map_name,
            "wasPlayed": self.was_played,
            "homeScore": self.home_score,
            "awayScore": self.away_score
        }


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
                    name: str | None = None,
                    epoch: float | None = None,
                    forfeit: bool | None = None,
                    event: SiteID | None = None,
                    home_team: SiteID | None = None,
                    away_team: SiteID | None = None) -> None:
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

    def to_dict(self) -> dict:
        return {
            "matchId": self.match_id.to_dict(),
            "matchName": self.name,
            "matchTime": self.epoch,
            "wasForfeit": self.was_forfeit,
            "event": self.event_id.to_dict(),
            "homeTeam": self.home_team.to_dict(),
            "awayTeam": self.away_team.to_dict(),
            "maps": [map_.to_dict() for map_ in self.maps]
        }
