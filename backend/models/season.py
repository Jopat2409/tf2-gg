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
    season_type: Mapped[String] = mapped_column(String, nullable=True)

    matches: Mapped[List[Match]] = relationship(back_populates="season")


