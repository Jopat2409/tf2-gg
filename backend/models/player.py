from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy import Integer, String, Boolean
from typing import List, TYPE_CHECKING

from database import Base

from utils.logger import Logger

player_logger = Logger.get_logger()

if TYPE_CHECKING:
    from models import Roster
else:
    Roster = "Roster"

class Player(Base):
    __tablename__ = "players"
    steam_id: Mapped[Integer] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[String] = mapped_column(String, nullable=True)
    forename: Mapped[String] = mapped_column(String, nullable=True)
    surname: Mapped[String] = mapped_column(String, nullable=True)
    is_banned: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
    is_verified: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
    avatar: Mapped[String] = mapped_column(String, nullable=True)
    rosters: Mapped[List[Roster]] = relationship("RosterPlayerAssociation", back_populates="player")
    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)

    def __init__(self,
                steam_id: int,
                display_name: str | None = None,
                forename: str | None = None,
                surname: str | None = None,
                banned: bool | None = None,
                verified: bool | None = None,
                avatar: str | None = None):
        self.steam_id = int(steam_id)
        self.display_name = display_name
        self.forename = forename
        self.surname = surname
        self.is_banned = banned
        self.is_verified = verified
        self.avatar = avatar

    @staticmethod
    def insert(session: scoped_session,
                steam_id: int,
                display_name: str | None = None,
                forename: str | None = None,
                surname: str | None = None,
                banned: bool | None = None,
                verified: bool | None = None,
                avatar: str | None = None,
                commit: bool = True) -> Player | None:

        if Player.get_player(steam_id):
            player_logger.log_warn(f"Attempting to insert player {steam_id}, which is already present in the database")
            return None

        player = Player(steam_id, display_name, forename, surname, banned, verified, avatar)
        session.add(player)

        if commit:
            session.commit()
        return player

    @staticmethod
    def get_or_insert(session: scoped_session,
                        steam_id: int,
                        commit: bool = True) -> Player | None:
        player = Player.get(steam_id)
        if not player:
            player = Player.insert(session, steam_id=steam_id, commit=commit)
        return player

    @staticmethod
    def get(steam_id: int) -> Player | None:
        return Player.query.filter(Player.steam_id == int(steam_id)).first() or None

    def to_dict(self) -> dict:
        return {
            "steamId": self.steam_id,
            "displayName": self.display_name,
            "isBanned": self.is_banned,
            "isVerified": self.is_verified,
            "avatar": self.avatar,
        }
