from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship, scoped_session
from sqlalchemy import Integer, Boolean, Float, String
from typing import List, TYPE_CHECKING

from database import Base
from utils.decorators import cache_ids
from utils.typing import SiteID, TfSource
from utils.logger import Logger

if TYPE_CHECKING:
    from models import Match
else:
    Match = "Match"

@cache_ids("season_id")
class Season(Base):
    __tablename__ = "seasons"

    season_id: Mapped[Integer] = mapped_column(Integer, primary_key=True, autoincrement=True)

    rgl_season_id: Mapped[Integer] = mapped_column(Integer, unique=True, nullable=True)
    etf2l_season_id: Mapped[Integer] = mapped_column(Integer, unique=True, nullable=True)
    ugc_season_id: Mapped[Integer] = mapped_column(Integer, unique=True, nullable=True)

    season_name: Mapped[String] = mapped_column(String, nullable=True)
    season_format: Mapped[String] = mapped_column(String, nullable=True)

    matches: Mapped[List[Match]] = relationship("Match", back_populates="season")

    def __init__(self,
                    event_id: SiteID,
                    name: str | None = None,
                    format_: str | None = None) -> None:
        self.season_id = self.get_next_id()
        if event_id.get_source() == TfSource.RGL:
            self.rgl_season_id = event_id.get_id()
        elif event_id.get_source() == TfSource.ETF2L:
            self.etf2l_season_id = event_id.get_id()
        elif event_id.get_source() == TfSource.UGC:
            self.ugc_season_id = event_id.get_id()

        self.season_name = name
        self.season_format = format_

    @staticmethod
    def get(season_id: int) -> Season | None:
        return Season.query.filter(Season.season_id == int(season_id)).first() or None

    @staticmethod
    def get_fromsource(event_id: SiteID) -> Season | None:
        if event_id.get_source() == TfSource.RGL:
            return Season.query.filter(Season.rgl_season_id == event_id.get_id()).first()
        if event_id.get_source() == TfSource.ETF2L:
            return Season.query.filter(Season.etf2l_season_id == event_id.get_id()).first()
        if event_id.get_source() == TfSource.UGC:
            return Season.query.filter(Season.ugc_season_id == event_id.get_id()).first()
        return None


