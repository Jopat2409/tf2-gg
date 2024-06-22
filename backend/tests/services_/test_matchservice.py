import json
import requests

from utils.typing import TfSource
from utils.file import read_required
from utils.scraping import TfDataDecoder

from services import MatchService

def test_get_last_etf2l_page():
    last_page = MatchService.get_last_etf2l_match_page()
    assert requests.get(f"https://api-v2.etf2l.org/matches?page={last_page}").json()["results"]["next_page_url"] is None
    assert not requests.get(f"https://api-v2.etf2l.org/matches?page={last_page + 1}").json()["results"]["data"]

def test_scrape_etf2l_matches():
    matches = MatchService.scrape_etf2l_matches([1,2])
    with open("tests\\test_data\\test_etf2l_data.json", "r", encoding='utf-8') as f:
        correct_matches = json.load(f)["matches"]
    first_match = TfDataDecoder.decode_match(TfSource.ETF2L, correct_matches[0])
    last_match = TfDataDecoder.decode_match(TfSource.ETF2L, correct_matches[1])
    assert len(matches) == 40
    assert matches[0] == first_match
    assert matches[-1] == last_match

    matches = MatchService.scrape_etf2l_matches([-2,-1,1,2])

    assert matches[0] == first_match
    assert matches[-1] == last_match

def test_scrape_rgl_page():
    assert MatchService.scrape_rgl_match_page(-1000, 2000) == []
    assert MatchService.scrape_rgl_match_page(0, -50) == []
    assert len(MatchService.scrape_rgl_match_page(0, 50)) == 50
    
    test_values = MatchService.scrape_rgl_match_page(2999, 25)
    assert test_values[0].get_id() == 3619
    assert test_values[-1].get_id() == 3646

def test_scrape_rgl_ids():
    assert MatchService.scrape_rgl_match_ids(from_=24000) == []
    last_match_id = MatchService.scrape_rgl_match_ids(from_=23e3)[-1]
    assert requests.get(f"https://api.rgl.gg/v0/matches/{last_match_id.get_id() + 1}").status_code == 404

def test_scrape_rgl_matches():
    matches = MatchService.scrape_rgl_matches([32])
    correct_matches = read_required("tests\\test_data\\test.json", json=True)["test_util_data"]["matches"]
    assert matches[0] == TfDataDecoder.decode_match(TfSource.RGL, correct_matches["32"])

    matches = MatchService.scrape_rgl_matches([32, 32, 32, 32, 32])
    assert len(matches) == 5
    assert all(match == TfDataDecoder.decode_match(TfSource.RGL, correct_matches["32"]) for match in matches)