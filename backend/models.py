from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from typing import List
from database import Base

class Player(Base):
    __tablename__ = 'players'
    player_id: Mapped[Integer] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[String] = mapped_column(String)
    forename: Mapped[String] = mapped_column(String)
    surname: Mapped[String] = mapped_column(String)

class Team(Base):
    __tablename__ = 'teams'
    team_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True)
    display_name: Mapped[String] = mapped_column(String)
    display_tag: Mapped[String] = mapped_column(String)
    rosters: Mapped[List["Roster"]] = relationship(back_populates="team")

    def __init__(self, display_name: str, display_tag: str):
        self.display_name = display_name
        self.display_tag = display_tag

class Roster(Base):
    __tablename__ = 'rosters'
    team_id: Mapped[Integer] = mapped_column(ForeignKey("teams.team_id"), primary_key=True)
    team: Mapped["Team"] = relationship(back_populates="rosters")
    roster_iteration: Mapped[Integer] = mapped_column(Integer, primary_key=True)
    roster_id: Mapped[Integer] = mapped_column(Integer)
