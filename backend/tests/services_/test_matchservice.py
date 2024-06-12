from services import MatchService
import requests

def test_get_last_etf2l_page():
    last_page = MatchService.get_last_etf2l_match_page()
    assert requests.get(f"https://api-v2.etf2l.org/matches?page={last_page}").json()["results"]["next_page_url"] is None
    assert not requests.get(f"https://api-v2.etf2l.org/matches?page={last_page + 1}").json()["results"]["data"]
