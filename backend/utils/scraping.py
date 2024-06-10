from typing import Any
import requests
import time
from multiprocessing import Pool
from models import Match, Roster
from utils.typing import TfSource, SiteID
from utils import epoch_from_timestamp

def post_request(url: str, default: Any = {}, **kwargs) -> tuple[int, dict]:
    """
    Send a POST request to the given `url`, with POST parameters as `kwargs`

    params:
        url[str]: url to send the POST request to
        default[any]: default value to return upon status code other than `200`
        **kwargs[dict]: parameters to be passed in to the POST request

    returns:
        (status_code[int], data[json]): the status code of the request and the data (or `default` if failure)
    """
    headers = {'accept': '*/*'}
    response = requests.post(url, params=kwargs, headers=headers, json={})
    return (response.status_code, response.json() if response.status_code == 200 else default)

def sleep_then_request(data) -> dict:
    time.sleep(data[1])
    return requests.get(data[0])

def get_first(urls: list[str], n: int) -> list[str]:
    return urls if n >= len(urls) else urls[:n]

def scrape_parallel(urls: list[str], batch_size: int, delay_step: float = 0.2, delay_size: int = 1):
    """
    BEST PARAMS: delay_step 0.2 delay_size 1 for RGL
                    delay_step 0.2 delay_size 5 for ETF2L
    """
    # dont change input
    urls = urls.copy()
    # optimal: delay_size 1 with 0.2
    with Pool(batch_size) as p:
        finished = False
        while not finished:
            to_process = get_first(urls, batch_size)
            delay_profile = [delay_step*(i//delay_size) for i in range(len(to_process))]
            results = p.map(sleep_then_request, zip(to_process, delay_profile))

            # remove successful urls
            success = [i for i, result in enumerate(results) if result.status_code == 200]
            # reverse indexes so deletion actually works :D
            for index in reversed(success):
                del urls[index]

            if not urls:
                finished = True

            yield [result.json() for result in results if result.status_code == 200]
        # yield results, remove all successful ones

def find_optimal_scraping_params(test_url: str, start_delay_size: int = 1, end_delay_size: int = 5, delay_start: float = 0.1, delay_end: float = 1.0, delay_step: float = 0.1) -> tuple:
    """
    Automatically finds the best combination of parameters to minimize the time to scrape
    """
    urls = [test_url for _ in range(9)]
    fastest = {}
    for delay_size in range(start_delay_size, end_delay_size + 1):

        current_delay = delay_start
        while current_delay <= delay_end:
            print(f"Testing {current_delay} delay for a batch of {delay_size}", end="\r")
            start_timer = time.perf_counter()
            for i in scrape_parallel(urls, batch_size=9, delay_step=current_delay, delay_size=delay_size):
                pass
            fastest.update({(delay_size, current_delay): time.perf_counter() - start_timer})
            current_delay += delay_step

    best_combo = min(fastest, key=fastest.get)
    return {"delay_size": best_combo[0], "delay_step": best_combo[1]}
        # Increment delay step until all 10 status codes are 200

class TfDataDecoder:
    """
    Class for decoding API data into ORM models
    """

    @staticmethod
    def __decode_rgl_match(match_data: dict) -> Match:
        match = Match(
            SiteID.rgl_id(match_data["matchId"]),
            epoch_from_timestamp(match_data.get("matchDate", 0)) or None,
            match_data.get("matchName", None),
            match_data.get("isForfeit", None),
            SiteID.rgl_id(match_data.get("seasonId", None)),
            SiteID.rgl_id(match_data.get("divisionId", None)),
            SiteID.rgl_id(match_data.get("regionId", None))
        )
        home_team, away_team = match_data.get("teams", ({}, {}))

        if not home_team or not away_team:
            return match

        for map_ in match_data.get("maps", []):
            match.add_map(map_["mapName"], SiteID.rgl_id(home_team["teamId"]), map_["homeScore"], SiteID.rgl_id(away_team["teamId"]), map_["awayScore"])
        return match

    def __decode_etf2l_match(match_data: dict) -> Match:
        match = Match(
            SiteID.etf2l_id(match_data["id"]),
            float(match_data.get("time", 0)) or None,
            match_data.get("competition", {}).get("name", None),
            match_data.get("defaultwin", None),
            SiteID.etf2l_id(match_data.get("competition", {}).get("id", None))
        )

    @staticmethod
    def decode_match(source: TfSource, match_data: dict) -> Match:
        if source == TfSource.RGL:
            return TfDataDecoder.__decode_rgl_match(match_data)

    @staticmethod
    def decode_roster(source: TfSource, roster_data: dict) -> Roster:
        return None
