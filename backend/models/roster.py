from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy import Integer, Boolean, Float, String, ForeignKey
from typing import List, TYPE_CHECKING

from utils.decorators import cache_ids, site_resource
from utils.typing import SiteID, TfSource
from utils.logger import Logger
from database import Base

# Prevent circular imports while maintaining typing
if TYPE_CHECKING:
    from models import Team, Player, MatchResult
else:
    Team = "Team"
    Player = "Player"
    MatchResult = "MatchResult"

roster_logger = Logger.get_logger()

@cache_ids("roster_id")
@site_resource("rgl_team_id", "etf2l_team_id", "ugc_team_id")
class Roster(Base):
    __tablename__ = "rosters"
    roster_id: Mapped[Integer] = mapped_column(ForeignKey("teams.team_id"), primary_key=True, autoincrement=True) # Internal roster id

    team_id: Mapped[Integer] = mapped_column(ForeignKey("teams.team_id"), nullable=True) # Internal team id
    team: Mapped[Team] = relationship(back_populates="rosters", foreign_keys=team_id)

    rgl_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # RGL site team ID
    etf2l_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # ETF2L Guild ID
    ugc_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # UGC guild ID

    roster_name: Mapped[String] = mapped_column(String, nullable=True)
    roster_tag: Mapped[String] = mapped_column(String, nullable=True)
    created_at: Mapped[Float] = mapped_column(Float, nullable=True)
    updated_at: Mapped[Float] = mapped_column(Float, nullable=True)

    players: Mapped[List[Player]] = relationship("RosterPlayerAssociation", back_populates="roster")
    match_results: Mapped[List[MatchResult]] = relationship("MatchResult")

    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)

    def __init__(self,
                    roster_id: SiteID,
                    team_id: int | None = None,
                    name: str | None = None,
                    tag: str | None = None,
                    created: float | None = None,
                    updated: float | None = None):

        self.roster_id = int(Roster.get_next_id())
        self.set_source_id(roster_id)

        # Construct the team
        if team_id is not None:
            from models import Team
            self.team = Team(team_id)
            self.team_id = self.team.team_id

        self.roster_name = name
        self.roster_tag = tag
        self.created_at = created
        self.updated_at = updated

    def stage(self, session: scoped_session) -> None:
        # stage self
        if not Roster.get(self.roster_id):
            session.add(session.merge(self))

    @staticmethod
    def insert(session: scoped_session,
                roster_id: SiteID,
                name: str | None = None,
                tag: str | None = None,
                created: float | None = None,
                updated: float | None = None,
                related_rosters: list[SiteID] = [],
                recursive: bool = False,
                commit: bool = True) -> bool:

        # If roster already exists, return
        if Roster.get_fromsource(roster_id):
            roster_logger.log_warn(f"Attempting to insert roster {roster_id} that already exists!")
            return False
        # Determine team
        from models import Team
        team_id = None
        related_team_ids = [Roster.get_fromsource(roster).team_id for roster in related_rosters]
        if not related_team_ids and recursive:
            team = Team()
            session.add(team)
            team_id = team.team_id
        elif related_team_ids:
            team_id = related_team_ids[0]

        roster = Roster(roster_id, team_id, name, tag, created, updated)
        session.add(roster)
        if commit:
            session.commit()

        return bool(Roster.get_fromsource(roster_id)) if commit else True

    @staticmethod
    def get_or_insert(session: scoped_session,
                        roster_id: SiteID,
                        commit: bool = True) -> Roster | None:
        roster = Roster.get_fromsource(roster_id)
        if roster:
            return roster

        success = Roster.insert(session, roster_id, commit=commit)
        if not success:
            return None
        return Roster.get_fromsource(roster_id)

    @staticmethod
    def get(roster_id: int) -> Roster | None:
        return Roster.query.filter(Roster.roster_id == int(roster_id)).first() or None

    @staticmethod
    def get_fromsource(roster_id: SiteID) -> Roster | None:
        if roster_id.get_source() == TfSource.RGL:
            return Roster.query.filter(Roster.rgl_team_id == int(roster_id.get_id())).first() or None

    def add_player(self, player: Player) -> bool:
        self.players.append(player)

    def add_player_by_id(self, steam_id: int, create: bool=True) -> bool:

        from models import Player

        player: Player = Player.query.filter(Player.steam_id == int(steam_id))

        if not player and not create:
            return False
        elif not player:
            player = Player.insert(steam_id)

        self.players.append(player)
        return True

    @staticmethod
    def get_incomplete() -> list[Roster]:
        return Roster.query.filter(Roster.rgl_team_id is not None, Roster.is_complete == 0)

    @staticmethod
    def count() -> int:
        return len(Roster.query.all())

    def __repr__(self) -> str:
        return f"""RosterId: {self.roster_id}, SourceId: {self.get_source_id()}"""
