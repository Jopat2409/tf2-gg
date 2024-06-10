from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy import Integer, Boolean, Float, String
from typing import List, TYPE_CHECKING

from database import Base
from utils.decorators import cache_ids
from utils.typing import SiteID, TfSource
from utils.logger import Logger

if TYPE_CHECKING:
    from models import MatchResult, Roster, Season
else:
    MatchResult = "MatchResult"
    Roster = "Roster"
    Season = "Season"

match_logger = Logger.get_logger()

@cache_ids("match_id")
class Match(Base):
    __tablename__ = "matches"
    match_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True) # Internal match ID

    rgl_match_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # RGL site match ID
    etf2l_match_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # ETF2L site guild ID
    ugc_match_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # UGC site guild ID

    match_epoch: Mapped[Float] = mapped_column(Float, nullable=True)
    match_name: Mapped[String] = mapped_column(String, nullable=True)
    was_forfeit: Mapped[Boolean] = mapped_column(Boolean, nullable=True)

    season_id: Mapped[Integer] = mapped_column(Integer, nullable=True)
    season: Mapped[Season] = relationship(back_populates="matches", foreign_keys=season_id)

    division_id: Mapped[Integer] = mapped_column(Integer, nullable=True)
    region_id: Mapped[Integer] = mapped_column(Integer, nullable=True)

    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)
    results: Mapped[List[MatchResult]] = relationship("MatchResult", back_populates="match")

    def __init__(self,
                    match_id: SiteID,
                    epoch: float | None = None,
                    name: str | None = None,
                    forfeit: bool | None = None,
                    season: SiteID | None = None,
                    division: SiteID | None = None,
                    region: SiteID | None = None) -> None:
        self.ID_MAPPING = {
            TfSource.RGL: "rgl_match_id",
            TfSource.UGC: "ugc_match_id",
            TfSource.ETF2L: "etf2l_match_id"
        }
        self.match_id = Match.get_next_id()
        setattr(self, self.ID_MAPPING[match_id.get_source()], match_id.get_id())
        self.match_epoch = epoch
        self.match_name = name
        self.was_forfeit = bool(forfeit) if forfeit is not None else None
        self.season_id = season.get_id() if season else None
        self.division_id = division.get_id() if division else None
        self.region_id = region.get_id() if region else None

    @staticmethod
    def insert(session: scoped_session,
                match_id: SiteID,
                commit: bool = True,
                epoch: float | None = None,
                name: str | None = None,
                forfeit: bool | None = None,
                season: SiteID | None = None,
                division: SiteID | None = None,
                region: SiteID | None = None) -> Match | None:

        # Block attempts to insert matches with the same match ID
        if Match.get_fromsource(match_id):
            match_logger.log_warn(f"Attempting to insert match {match_id} when this match already exists")
            return None

        # Create and add match
        match = Match(match_id, epoch, name, forfeit, season, division, region)
        session.add(match)

        # Commit if applicable
        if commit:
            session.commit()

        # If we have commited then success if change reflected, else assume success
        return Match.get_fromsource(match_id) if commit else match


    @staticmethod
    def update(session: scoped_session, other: Match, commit: bool = True) -> bool:
        to_update = Match.get_fromsource(other.get_site_id())

        if not to_update:
            return False

        to_update.match_name = other.match_name
        to_update.match_epoch = other.match_epoch
        to_update.was_forfeit = other.was_forfeit
        to_update.season_id = other.season_id
        to_update.division_id = other.division_id
        to_update.region_id = other.region_id

        to_update.is_complete = other.is_complete

        from models import MatchResult, Roster
        for result in other.results:
            #TODO: check if map result already staged
            if not MatchResult.get(result.match_id, result.roster_id, result.map_name):
                session.add(session.merge(result))
            if not Roster.get(result.roster_id):
                session.add(session.merge(result.roster))

        to_update.results = other.results
        if commit:
            session.commit()

        return True

    @staticmethod
    def get_or_insert(session: scoped_session,
                        match_id: SiteID,
                        commit: bool = True) -> Match | None:

        match = Match.get_fromsource(match_id)

        # Insert match if not found
        if not match:
            match = Match.insert(session, match_id, commit=commit)

        return match

    @staticmethod
    def get_fromsource(match_id: SiteID) -> Match:
        if match_id.get_source() == TfSource.RGL:
            return Match.query.filter(Match.rgl_match_id == match_id.get_id()).first()
        #TODO Implement other ones

    def get_site_id(self) -> SiteID:
        return SiteID.rgl_id(self.rgl_match_id) if self.rgl_match_id is not None else SiteID(TfSource.UGC, self.rgl_match_id)

    @staticmethod
    def get(match_id: int) -> Match | None:
        return Match.query.filter(Match.match_id == int(match_id)).first()

    def add_map(self, map_name: str, home_team: SiteID, home_score: int, away_team: SiteID, away_score: int) -> None:
        from models import Roster, MatchResult
        # Get internal IDs of the home and away team
        home_roster = Roster.get_fromsource(home_team) or Roster(home_team)
        away_roster = Roster.get_fromsource(away_team) or Roster(away_team)

        # Add to list of match results
        self.results.append(MatchResult(self.match_id, home_roster, map_name, home_score))
        self.results.append(MatchResult(self.match_id, away_roster, map_name, away_score))

    def json(self) -> dict:
        return {
            "matchName": self.match_name,
            "matchDate": self.match_epoch,
            "wasForfeit": self.was_forfeit,
            "maps": [result.json for result in self.results]
        }

    @staticmethod
    def get_count(league: TfSource) -> int:
        if league == TfSource.RGL:
            return Match.query.filter(Match.rgl_match_id is not None).count()

    @staticmethod
    def get_incomplete(league: TfSource) -> list[Match]:
        if league == TfSource.RGL:
            return Match.query.filter(Match.rgl_match_id is not None, not Match.is_complete).all()


    @staticmethod
    def get_matches(team_id: int = None) -> list[Match]:
        from models import MatchResult

        return [match.json() for match in Match.query.filter(Match.results.any(MatchResult.roster_id == int(team_id))).all()]

    def __repr__(self) -> str:
        return f"""MatchId: {self.match_id}, SourceId: {self.get_site_id()}, MatchName: {self.match_name}, Complete: {self.is_complete}"""
