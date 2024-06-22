import json
import time
import requests

from typing import Any
from multiprocessing import Pool

from db.team import Team
from db.match import Match

from utils import epoch_from_timestamp
from utils.typing import TfSource, SiteID

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
    """
    Sleeps then requests
    """
    time.sleep(data[1])
    return requests.get(data[0])

def get_first(urls: list[str], n: int) -> list[str]:
    """
    Returns the first n items in a list
    """
    return urls if n >= len(urls) else urls[:n]

def scrape_parallel(urls: list[str], batch_size: int, delay_step: float = 0.2, delay_size: int = 1, ignore_server_errors: bool = True):
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

            # remove Urls if the result wass successful, OR the URL caused a server error and we want to ignore server errors
            remove_codes = [200] + ([500] if ignore_server_errors else [])
            success = [i for i, result in enumerate(results) if result.status_code in remove_codes]
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

class TfDataDecoder(json.JSONDecoder):
    """
    Class for decoding API data into classes
    """
    @staticmethod
    def _decode_rgl_match(match_data: dict) -> Match:

        teams = match_data.get("teams", [])
        home_team = next((team for team in teams if team["isHome"]), teams[0])["teamId"]
        away_team = next(team for team in teams if team["teamId"] != home_team)["teamId"]

        match = Match(
            SiteID.rgl_id(match_data["matchId"]),
            match_data.get("matchName", None),
            epoch_from_timestamp(match_data.get("matchDate", 0)) or None,
            match_data.get("isForfeit", None),
            SiteID.rgl_id(match_data.get("seasonId", None)),
            SiteID.rgl_id(home_team),
            SiteID.rgl_id(away_team)
        )

        for map_ in match_data.get("maps", []):
            name, home_score, away_score = map_.get("mapName"), map_.get("homeScore"), map_.get("awayScore")
            match.add_map_data(name, home_score is None and away_score is None, home_score or 0, away_score or 0)

        return match

    @staticmethod
    def _decode_etf2l_match(match_data: dict) -> Match:

        match_name = match_data.get("competition", {}).get("name", "") + " " + match_data.get("round", "")

        home_team = match_data.get("clan1", {}).get("id", None)
        away_team = match_data.get("clan2", {}).get("id", None)

        match = Match(
            SiteID.etf2l_id(match_data["id"]),
            match_name,
            float(match_data.get("time", 0)) or None,
            match_data.get("defaultwin", None),
            SiteID.etf2l_id(match_data.get("competition", {}).get("id", None)),
            SiteID.etf2l_id(home_team),
            SiteID.etf2l_id(away_team)
        )

        for map_ in match_data.get("map_results", []):
            match.add_map_data(map_["map"], True, map_["clan1"], map_["clan2"])

        return match

    @staticmethod
    def _decode_internal_match(match_data: dict) -> Match:
        match = Match(
            SiteID(TfSource[match_data["matchId"]["source"]], match_data["matchId"]["id"]),
            match_data["matchName"],
            float(match_data["matchTime"] or 0),
            match_data["wasForfeit"],
            SiteID(TfSource[match_data["eventId"]["source"]], match_data["eventId"]["id"]),
            SiteID(TfSource[match_data["homeTeam"]["source"]], match_data["homeTeam"]["id"]),
            SiteID(TfSource[match_data["awayTeam"]["source"]], match_data["awayTeam"]["id"]),
        )
        for map_ in match_data["maps"]:
            match.add_map_data(map_["mapName"], map_["wasPlayed"], int(map_["homeScore"]), int(map_["awayScore"]))
        return match
    
    @staticmethod
    def _decode_rgl_team(team_data: dict) -> Team:
        return Team(
            SiteID.rgl_id(team_data["teamId"]),
            team_data.get("name", None),
            team_data.get("tag", None),
            epoch_from_timestamp(team_data.get("createdAt", 0)) or None,
            epoch_from_timestamp(team_data.get("updatedAt", 0)) or None,
            [SiteID.rgl_id(team) for team in team_data.get("linkedTeams", [])],
            [int(player["steamId"]) for player in team_data.get("players", [])]
        )
    
    @staticmethod
    def _decode_etf2l_team(team_data: dict) -> Team:
        return Team(
            SiteID.etf2l_id(team_data["id"]),
            team_data.get("name", None),
            team_data.get("tag", None),
            None,
            None,
            [],
            [int(player["steam"]["id64"]) for player in team_data.get("players", [])]
        )
    
    @staticmethod
    def _decode_internal_team(team_data: dict) ->Team:
        return Team(
            SiteID(TfSource[team_data["teamId"]["source"]], team_data["teamId"]["id"]),
            team_data["teamName"],
            team_data["teamTag"],
            float(team_data["createdAt"] or 0),
            float(team_data["updatedAt"] or 0),
            [SiteID(TfSource[team["source"]], team["id"]) for team in team_data.get("linkedTeams", [])],
            team_data["players"]
        )

    @staticmethod
    def decode_match(source: TfSource, match_data: dict) -> Match:
        func_ = getattr(TfDataDecoder, f"_decode_{source.name.lower()}_match")
        return func_(match_data)
    
    @staticmethod
    def decode_team(source: TfSource, team_data: dict) -> Team:
        func_ = getattr(TfDataDecoder, f"_decode_{source.name.lower()}_team")
        return func_(team_data)

    def object_hook(self, obj):
        if "match" in obj:
            return TfDataDecoder.decode_match(TfSource.INTERNAL, obj)
        if "team" in obj:
            return TfDataDecoder.decode_team(TfSource.INTERNAL, obj)
        return obj

class TfDataEncoder(json.JSONEncoder):

    def default(self, o: Any) -> Any:
        if isinstance(o, Match):
            return {"match": o.to_dict()}
        return super().default(o)
