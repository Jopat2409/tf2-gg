import json

from db.match import Map, Match

from utils.typing import SiteID, TfSource
from utils.scraping import TfDataDecoder, TfDataEncoder
from utils.file import read_required

def circular_decode(data):
    return json.loads(json.dumps(data, cls=TfDataEncoder), cls=TfDataDecoder)

def test_tfdata_encoder_map():
    test_map = Map("pl_badwater", True, 4, 5)
    assert circular_decode(test_map) == test_map

def test_tfdata_encoder_siteid():
    test_id = SiteID.rgl_id(32)
    assert circular_decode(test_id) == test_id

    test_id = SiteID.etf2l_id(32)
    assert circular_decode(test_id) == test_id

def test_tfdata_decode_match():
    test_match = {"matchId": 32}
    assert TfDataDecoder.decode_match(TfSource.RGL, test_match).match_id == SiteID.rgl_id(32)

    test_match = TfDataDecoder.decode_match(TfSource.RGL, read_required("tests\\test_data\\test.json", json=True)["test_util_data"]["matches"]["32"])
    assert test_match.match_id == SiteID.rgl_id(32)
    assert test_match.name == "Week 1 - Badwater"
    assert test_match.event_id == SiteID.rgl_id(1)
    assert len(test_match.maps) == 1
    assert test_match.maps[0] == Map("pl_badwater_pro_v9", True, 2, 0)

    assert test_match.home_team == SiteID.rgl_id(54)
    assert test_match.away_team == SiteID.rgl_id(41)

def test_tfdata_encoder_match():
    test_match = Match(SiteID.rgl_id(32))
    assert circular_decode(test_match) == test_match

    test_match = Match(SiteID.etf2l_id(32))
    assert circular_decode(test_match) == test_match

    test_match = TfDataDecoder.decode_match(TfSource.RGL, read_required("tests\\test_data\\test.json", json=True)["test_util_data"]["matches"]["32"])
    assert circular_decode(test_match) == test_match
