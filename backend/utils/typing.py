from __future__ import annotations

from enum import IntEnum

class TfSource(IntEnum):
    RGL = 1,
    UGC = 2,
    ETF2L = 3,
    INERNAL = 4

class SiteID:

    def __init__(self, id_: int, source: TfSource):
        self.__id = int(id_)
        self.__source = source

    def get_id(self) -> int:
        return self.__id

    def get_source(self) -> TfSource:
        return self.__source

    def __eq__(self, other: SiteID) -> bool:
        if not isinstance(other, SiteID):
            return False
        return other.get_source() == self.get_source() and other.get_id() == self.get_id()

    def __neq__(self, other: SiteID) -> bool:
        return not self == other

    @staticmethod
    def rgl_id(id_: int) -> SiteID | None:
        if id_ is None:
            return None
        return SiteID(id_, TfSource.RGL)

    @staticmethod
    def etf2l_id(id_: int) -> SiteID | None:
        if id_ is None:
            return None
        return SiteID(id_, TfSource.ETF2L)

    def __repr__(self) -> str:
        return f"""({self.__source.name} ID: {self.__id})"""

    def to_dict(self) -> dict:
        return {
            "source": self.get_source().name,
            "id": self.get_id()
        }
