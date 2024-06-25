import time
import json

from db.match import Map, Match
from db.team import Team

from utils.typing import SiteID, TfSource
from utils.scraping import TfDataDecoder, TfDataEncoder, scrape_parallel, sleep_then_request, get_first
from utils.file import read_required

def test_sleep_then_request():
    start_time = time.perf_counter()
    sleep_then_request(("https://www.google.com", 1.0))
    assert time.perf_counter() - start_time > 1

def test_get_first():

    test = [f"test{i}" for i in range(10)]
    assert get_first(test, 1) == ["test0"]
    assert get_first(test, 0) == []
    assert get_first(test, 10) == test

    test2 = ["hello :)"]
    assert get_first(test2, 10) == test2

    assert get_first([], 10) == []

def test_scrape_parallel():
    test_matches = [f"https://api.rgl.gg/v0/matches/{_id}" for _id in [32, 33, 34, 35, 36, 37, 38, 39, 40]]

    # test even number of batch size
    results = []
    for result in scrape_parallel(test_matches, 3):
        results += result

    assert len(results) == 9

    # Test batch size not divisible by length
    results = []
    for result in scrape_parallel(test_matches, 4):
        print(result)
        results += result

    assert len(results) == 9

    # Test batch size bigger than length
    results = []
    for result in scrape_parallel(test_matches, 10):
        results += result

    assert len(results) == 9

def test_tfdata_encode_map():
    """
    Tests the JSON encoding function used to encode `Map` objects
    """
    assert json.dumps(Map("pl_badwater", True, 4, 5), cls=TfDataEncoder) == """{"map": {"mapName": "pl_badwater", "wasPlayed": true, "homeScore": 4, "awayScore": 5}}"""
    assert json.dumps(Map("koth_bagel_rc6", False), cls=TfDataEncoder) == """{"map": {"mapName": "koth_bagel_rc6", "wasPlayed": false, "homeScore": null, "awayScore": null}}"""
    assert json.dumps(Map("koth_bagel_rc6", False, 1, 2), cls=TfDataEncoder) == """{"map": {"mapName": "koth_bagel_rc6", "wasPlayed": false, "homeScore": null, "awayScore": null}}"""

def test_tfdata_encode_id():
    """
    Tests the JSON encoding function used to encode `SiteID` objects
    """
    assert json.dumps(SiteID.rgl_id(32), cls=TfDataEncoder) == """{"source": {"site": "RGL", "id": 32}}"""
    assert json.dumps(SiteID.etf2l_id(32), cls=TfDataEncoder) == """{"source": {"site": "ETF2L", "id": 32}}"""
    assert json.dumps(SiteID.etf2l_id(None), cls=TfDataEncoder) == 'null'

def test_tfdata_encode_match():
    """
    Tests the JSON encoding function used to encode `Match` objects
    """
    assert json.dumps(Match(SiteID.rgl_id(32)), cls=TfDataEncoder) == """{"match": {"matchId": {"source": {"site": "RGL", "id": 32}}, "matchName": null, "matchTime": null, "wasForfeit": null, "event": null, "homeTeam": null, "awayTeam": null, "maps": []}}"""
    assert json.dumps(Match(SiteID.etf2l_id(32)), cls=TfDataEncoder) == """{"match": {"matchId": {"source": {"site": "ETF2L", "id": 32}}, "matchName": null, "matchTime": null, "wasForfeit": null, "event": null, "homeTeam": null, "awayTeam": null, "maps": []}}"""

    rgl_match = Match(SiteID.rgl_id(32), "Rewind 2 Grand Finals", 1497490200.0, False, SiteID.rgl_id(30), SiteID.rgl_id(41), SiteID.rgl_id(54))
    rgl_match.add_map(Map("pl_badwater", True, 1, 4))
    assert json.dumps(rgl_match, cls=TfDataEncoder) == """{"match": {"matchId": {"source": {"site": "RGL", "id": 32}}, "matchName": "Rewind 2 Grand Finals", "matchTime": 1497490200.0, "wasForfeit": false, "event": {"source": {"site": "RGL", "id": 30}}, "homeTeam": {"source": {"site": "RGL", "id": 41}}, "awayTeam": {"source": {"site": "RGL", "id": 54}}, "maps": [{"map": {"mapName": "pl_badwater", "wasPlayed": true, "homeScore": 1, "awayScore": 4}}]}}"""

    etf2l_match = Match(SiteID.etf2l_id(32), "Rewind 2 Grand Finals", 1497490200.0, False, SiteID.etf2l_id(30), SiteID.etf2l_id(41), SiteID.etf2l_id(54))
    etf2l_match.add_map(Map("pl_badwater", True, 1, 4))
    assert json.dumps(etf2l_match, cls=TfDataEncoder) == """{"match": {"matchId": {"source": {"site": "ETF2L", "id": 32}}, "matchName": "Rewind 2 Grand Finals", "matchTime": 1497490200.0, "wasForfeit": false, "event": {"source": {"site": "ETF2L", "id": 30}}, "homeTeam": {"source": {"site": "ETF2L", "id": 41}}, "awayTeam": {"source": {"site": "ETF2L", "id": 54}}, "maps": [{"map": {"mapName": "pl_badwater", "wasPlayed": true, "homeScore": 1, "awayScore": 4}}]}}"""

def test_tfdata_encode_team():
    assert json.dumps(Team(SiteID.rgl_id(41)), cls=TfDataEncoder) == """{"team": {"teamId": {"source": {"site": "RGL", "id": 41}}, "teamName": null, "teamTag": null, "createdAt": null, "updatedAt": null, "players": [], "linkedTeams": []}}"""
    assert json.dumps(Team(SiteID.etf2l_id(41)), cls=TfDataEncoder) == """{"team": {"teamId": {"source": {"site": "ETF2L", "id": 41}}, "teamName": null, "teamTag": null, "createdAt": null, "updatedAt": null, "players": [], "linkedTeams": []}}"""

def test_tfdata_decode_map():
    test_map = {"mapName": "koth_bagel_rc6", "wasPlayed": True, "homeScore": 1, "awayScore": 2}
    correct_map = Map("koth_bagel_rc6", True, 1, 2)
    assert TfDataDecoder.decode_map(TfSource.RGL, test_map) == correct_map
    assert json.loads(json.dumps({"map": test_map}), cls=TfDataDecoder) == correct_map


def test_tfdata_decode_match():

    # Test Simple decoding with just match ID
    test_match_rgl = {"matchId": 32}
    test_match_etf2l = {"id": 32}
    correct_match_rgl = Match(SiteID.rgl_id(32), None, None, None, None, None, None)
    correct_match_etf2l = Match(SiteID.etf2l_id(32), None, None, None, None, None, None)

    assert TfDataDecoder.decode_match(TfSource.RGL, test_match_rgl) == correct_match_rgl
    assert TfDataDecoder.decode_match(TfSource.ETF2L, test_match_etf2l) == correct_match_etf2l
    assert json.loads(json.dumps({"match": {"matchId": {"source": {"id": 32, "site": "RGL"}}}}), cls=TfDataDecoder) == correct_match_rgl
    assert json.loads(json.dumps({"match": {"matchId": {"source": {"id": 32, "site": "ETF2L"}}}}), cls=TfDataDecoder) == correct_match_etf2l


    test_match_rgl = TfDataDecoder.decode_match(TfSource.RGL, read_required("tests\\test_data\\test.json", json=True)["test_util_data"]["matches"]["32"])
    test_match_etf2l = TfDataDecoder.decode_match(TfSource.ETF2L, read_required("tests\\test_data\\test_etf2l_data.json", json=True)["matches"][0])
    correct_match_etf2l = Match(SiteID.etf2l_id(88728), "6v6 Season 47 (Spring 2024): Division 2 Grand Final", 1716750900.0, False, SiteID.etf2l_id(914), SiteID.etf2l_id(36044), SiteID.etf2l_id(32386))
    correct_match_rgl = Match(SiteID.rgl_id(32), "Week 1 - Badwater", 1497490200.0, False, SiteID.rgl_id(1), SiteID.rgl_id(54), SiteID.rgl_id(41))
    correct_match_rgl.add_map(Map("pl_badwater_pro_v9", True, 2, 0))

    assert test_match_rgl == correct_match_rgl
    assert test_match_etf2l == correct_match_etf2l
