from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import Integer
from typing import List, TYPE_CHECKING, Optional

from database import Base
from utils.decorators import cache_ids, staged_model

if TYPE_CHECKING:
    from models import Roster
else:
    Roster = "Roster"

@staged_model("team_id")
@cache_ids("team_id")
class Team(Base):
    """
    Encapsulates a team as an entity rather than a collection of players. One team can have many `rosters`,
    and the `Team` model simply links related rosters together
    """
    __tablename__ = "teams"
    team_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True) # Internal team ID
    rosters: Mapped[List[Roster]] = relationship(back_populates="team", foreign_keys='Roster.team_id')

    def __init__(self,
                    team_id: Optional[int] = None) -> None:
        self.team_id = team_id or int(Team.get_next_id())

    @staticmethod
    def insert(session: scoped_session,
                team_id: Optional[int] = None,
                commit: bool = True) -> Team | None:
        """
        Inserts a single team into the database, stages the changes and commits if `commit` is specified as an argument

        params:
            session[scoped_session]: The session to add / commit the team to
            commit[bool]: Whether or not to actually perform the commit (`true`) or just keep the changes staged (`false`)
        """

        # Populate the team
        team = Team(team_id)

        # If the team somehow already exists, return none
        if Team.get(team.team_id):
            return None

        # Stage and commit the changes (if specified)
        team.stage(session)
        if commit:
            session.commit()

        return team

    @staticmethod
    def get_or_insert(team_id: int,
                        session: scoped_session,
                        commit: bool = True) -> Team | None:
        """
        Gets the team given the team_id, or inserts it into the database if it does not already exist
        No idea why you would need to use this to be honest :D
        """
        team = Team.get(team_id)
        if not team:
            team = Team.insert(session, team_id=team_id, commit=commit)
        return team

    @staticmethod
    def get(team_id: int) -> Team | None:
        """
        Gets a single team given the team ID
        params:
            team_id[int]: the internal ID of the team to get
        returns:
            team[Team|None]: the team corresponding to the team ID, or none if the team does not exist
        """
        return Team.query.filter(Team.team_id == int(team_id)).first() or None

    @staticmethod
    def count() -> int:
        """
        Gets the number of teams present in the database
        """
        return len(Team.query.all())

    def __repr__(self) -> str:
        return f"""Team with ID {self.team_id}"""
