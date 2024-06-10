from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Float, ForeignKey
from typing import TYPE_CHECKING

from database import Base

if TYPE_CHECKING:
    from models import Player, Roster
else:
    Player = "Player"
    Roster = "Roster"

class RosterPlayerAssociation(Base):
    from models import Player, Roster
    __tablename__ = "roster_association_table"
    player_id: Mapped[Integer] = mapped_column(Integer, ForeignKey("players.steam_id"), primary_key=True)
    roster_id: Mapped[Integer] = mapped_column(Integer, ForeignKey("rosters.roster_id"), primary_key=True)
    joined_at: Mapped[Float] = mapped_column(Float, primary_key=True)
    left_at: Mapped[Float] = mapped_column(Float)

    player: Mapped[Player] = relationship("Player", back_populates="rosters")
    roster: Mapped[Roster]  = relationship("Roster", back_populates="players")

    def __init__(self, player: Player, roster: Roster, joined: float, left: float) -> None:
        self.player = player
        self.roster = roster
        self.joined_at = joined
        self.left_at = left
