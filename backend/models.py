from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean, Float, func, event
from utils.typing import SiteID, TfSource
from sqlalchemy.orm import scoped_session
from utils.logger import Logger
from utils.decorators import cache_ids
from typing import List
from database import Base

model_logger = Logger.get_logger()

class RosterPlayerAssociation(Base):
    __tablename__ = "roster_association_table"
    player_id: Mapped[Integer] = mapped_column(Integer, ForeignKey("players.steam_id"), primary_key=True)
    roster_id: Mapped[Integer] = mapped_column(Integer, ForeignKey("rosters.roster_id"), primary_key=True)
    joined_at: Mapped[Float] = mapped_column(Float, primary_key=True)
    left_at: Mapped[Float] = mapped_column(Float)

    player: Mapped["Player"] = relationship("Player", back_populates="rosters")
    roster: Mapped["Roster"]  = relationship("Roster", back_populates="players")

    def __init__(self, player: Player, roster: Roster, joined: float, left: float) -> None:
        self.player = player
        self.roster = roster
        self.joined_at = joined
        self.left_at = left

    @staticmethod
    def insert(session: scoped_session,
                player: int, roster: int,
                joined: float, left: float | None,
                commit: bool = True,
                recursive: bool = False) -> bool:

        player_obj = Player.get_or_insert(session, player, commit=commit) if recursive else Player.get(player)


class Player(Base):
    __tablename__ = "players"
    steam_id: Mapped[Integer] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[String] = mapped_column(String, nullable=True)
    forename: Mapped[String] = mapped_column(String, nullable=True)
    surname: Mapped[String] = mapped_column(String, nullable=True)
    is_banned: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
    is_verified: Mapped[Boolean] = mapped_column(Boolean, nullable=True)
    avatar: Mapped[String] = mapped_column(String, nullable=True)
    rosters: Mapped[List["Roster"]] = relationship("RosterPlayerAssociation", back_populates="player")
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
            model_logger.log_warn(f"Attempting to insert player {steam_id}, which is already present in the database")
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

@cache_ids("team_id")
class Team(Base):
    __tablename__ = "teams"
    team_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True) # Internal team ID
    rosters: Mapped[List["Roster"]] = relationship(back_populates="team", foreign_keys='Roster.team_id')

    def __init__(self) -> None:
        self.team_id = int(Team.get_next_id())

    @staticmethod
    def get(team_id: int) -> Team | None:
        return Team.query.filter(Team.team_id == int(team_id)).first() or None

@cache_ids("roster_id")
class Roster(Base):
    __tablename__ = "rosters"
    roster_id: Mapped[Integer] = mapped_column(ForeignKey("teams.team_id"), primary_key=True, autoincrement=True) # Internal roster id

    team_id: Mapped[Integer] = mapped_column(ForeignKey("teams.team_id"), nullable=True) # Internal team id
    team: Mapped["Team"] = relationship(back_populates="rosters", foreign_keys=team_id)

    rgl_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # RGL site team ID
    etf2l_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # ETF2L Guild ID
    ugc_team_id: Mapped[Integer] = mapped_column(Integer, nullable=True) # UGC guild ID

    roster_name: Mapped[String] = mapped_column(String, nullable=True)
    roster_tag: Mapped[String] = mapped_column(String, nullable=True)
    created_at: Mapped[Float] = mapped_column(Float, nullable=True)
    updated_at: Mapped[Float] = mapped_column(Float, nullable=True)

    players: Mapped[List["Player"]] = relationship("RosterPlayerAssociation", back_populates="roster")
    match_results: Mapped[List["MatchResult"]] = relationship("MatchResult")

    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)

    def __init__(self,
                    roster_id: SiteID,
                    team_id: int | None = None,
                    name: str | None = None,
                    tag: str | None = None,
                    created: float | None = None,
                    updated: float | None = None):
        self.roster_id = int(Roster.get_next_id())
        if roster_id.get_source() == TfSource.RGL:
            self.rgl_team_id = roster_id.get_id()
        elif roster_id.get_source() == TfSource.ETF2L:
            self.etf2l_team_id = roster_id.get_id()
        self.team_id = team_id
        self.roster_name = name
        self.roster_tag = tag
        self.created_at = created
        self.updated_at = updated

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
            model_logger.log_warn(f"Attempting to insert roster {roster_id} that already exists!")
            return False
        # Determine team
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
    division_id: Mapped[Integer] = mapped_column(Integer, nullable=True)
    region_id: Mapped[Integer] = mapped_column(Integer, nullable=True)

    is_complete: Mapped[Boolean] = mapped_column(Boolean, default=False)
    results: Mapped[List["MatchResult"]] = relationship("MatchResult", back_populates="match")

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
            model_logger.log_warn(f"Attempting to insert match {match_id} when this match already exists")
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

        return [match.json() for match in Match.query.filter(Match.results.any(MatchResult.roster_id == int(team_id))).all()]

    def __repr__(self) -> str:
        return f"""MatchId: {self.match_id}, SourceId: {self.get_site_id()}, MatchName: {self.match_name}, Complete: {self.is_complete}"""


class MatchResult(Base):
    __tablename__ = "match_results"

    match_id: Mapped[Integer] = mapped_column(ForeignKey("matches.match_id"), primary_key=True)
    match: Mapped["Match"] = relationship("Match", back_populates="results")

    roster_id: Mapped[Integer] = mapped_column(ForeignKey("rosters.roster_id"), primary_key=True)
    roster: Mapped["Roster"] = relationship("Roster", back_populates="match_results")

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
