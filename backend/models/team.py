from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer
from typing import List, TYPE_CHECKING

from database import Base
from utils.decorators import cache_ids

if TYPE_CHECKING:
    from models import Roster
else:
    Roster = "Roster"

@cache_ids("team_id")
class Team(Base):
    __tablename__ = "teams"
    team_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True) # Internal team ID
    rosters: Mapped[List[Roster]] = relationship(back_populates="team", foreign_keys='Roster.team_id')

    def __init__(self) -> None:
        self.team_id = int(Team.get_next_id())

    @staticmethod
    def get(team_id: int) -> Team | None:
        return Team.query.filter(Team.team_id == int(team_id)).first() or None
