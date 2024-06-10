from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from typing import TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models import Roster, Match
else:
    Roster = "Roster"
    Match = "Match"

class MatchResult(Base):
    __tablename__ = "match_results"

    match_id: Mapped[Integer] = mapped_column(ForeignKey("matches.match_id"), primary_key=True)
    match: Mapped[Match] = relationship("Match", back_populates="results")

    roster_id: Mapped[Integer] = mapped_column(ForeignKey("rosters.roster_id"), primary_key=True)
    roster: Mapped[Roster] = relationship("Roster", back_populates="match_results")

    map_name: Mapped[String] = mapped_column(String, primary_key=True)

    score: Mapped[Integer] = mapped_column(Integer)

    def __init__(self, match_id: int, team: Roster, map_name: str, score: int) -> None:
        self.match_id = match_id
        self.roster_id = team.roster_id
        self.roster = team
        self.map_name = map_name
        self.score = score

    def get(match: int, roster: int, map_: str) -> MatchResult | None:
        return MatchResult.query.filter(MatchResult.match_id == int(match) and MatchResult.roster_id == int(roster) and MatchResult.map_name == map_).first()

    def json(self) -> dict:
        return {
            "roster-id": self.roster_id,
            "map-name": self.map_name,
            "score": self.score
        }
