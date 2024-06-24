"""
Utility functions to use when scraping data from websites / APIs
"""
import json
import time
import requests

from typing import Any
from multiprocessing import Pool

from db.team import Team
from db.match import Match, Map

from utils import epoch_from_timestamp
from utils.typing import TfSource, SiteID

def post_request(url: str, default: Any = {}, **kwargs) -> tuple[int, dict]:
    """Send a POST request to the given `url`, with POST parameters as `kwargs`

    Args:
        url (str): The url to set the post request to
        default (Any, optional): the default value to be returned if the status code of the POST is not 200. Defaults to {}.

    Returns:
        tuple[int, dict]: the response status code and the response json (if the status code is 200) else `default`.
    """
    response = requests.post(url,
                                params=kwargs,
                                headers={'accept': '*/*'},
                                json={})
    return (response.status_code, response.json() if response.status_code == 200 else default)

def sleep_then_request(data: tuple) -> dict:
    """Sleeps for the given amount of time then sends a GET request to the url

    Args:
        data (tuple): tuple containing (url, delay)

    Returns:
        dict: the response from the GET request
    """
    time.sleep(data[1])
    return requests.get(data[0])

def get_first(urls: list[str], n: int) -> list[str]:
    """Retrieves the first `n` URLs from the list

    Args:
        urls (list[str]): list of urls
        n (int): number of urls to retrieve

    Returns:
        list[str]: list of the first n urls
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
    Custom JSON decoder for decoding API results into a format that is consistent between them all
    """

    @staticmethod
    def _decode_rgl_map(map_data: dict) -> Map:
        name, home_score, away_score = map_data.get("mapName"), map_data.get("homeScore"), map_data.get("awayScore")
        return Map(name, home_score is not None and away_score is not None, home_score or 0, away_score or 0)

    @staticmethod
    def _decode_etf2l_map(map_data: dict) -> Map:
        return Map(map_data["map"], True, map_data["clan1"], map_data["clan2"])

    @staticmethod
    def _decode_internal_map(map_: dict) -> Map:
        map_data = map_["map"]
        return Map(map_data["mapName"], map_data["wasPlayed"], map_data["homeScore"], map_data["awayScore"])

    @staticmethod
    def decode_map(source: TfSource, map_data: dict) -> Map:
        func_ = getattr(TfDataDecoder, f"_decode_{source.name.lower()}_map")
        return func_(map_data)

    @staticmethod
    def _decode_rgl_match(match_data: dict) -> Match:
        """Decodes a dictionary containing match data pulled from the RGL public API

        Args:
            match_data (dict): data pulled from the RGL API (or in the same format)

        Returns:
            Match: A match object encapsulating the RGL match data passed in
        """

        # Isolate the home and away team IDs
        teams = match_data.get("teams", [])
        home_team = next((team for team in teams if team["isHome"]), next(team for team in teams if team["teamId"] == match_data["winner"]))["teamId"] if teams else None
        away_team = next(team for team in teams if team["teamId"] != home_team)["teamId"] if teams else None

        # Initialise the match with as much data as possible
        match = Match(
            SiteID.rgl_id(match_data["matchId"]),
            match_data.get("matchName", None),
            epoch_from_timestamp(match_data.get("matchDate", 0)) or None,
            match_data.get("isForfeit", None),
            SiteID.rgl_id(match_data.get("seasonId", None)),
            SiteID.rgl_id(home_team),
            SiteID.rgl_id(away_team)
        )

        # Add map results if they exist in the data given
        for map_ in match_data.get("maps", []):
            match.add_map(TfDataDecoder.decode_map(TfSource.RGL, map_))

        return match

    @staticmethod
    def _decode_etf2l_match(match_data: dict) -> Match:
        """Decodes a dictionary containing match data pulled from the ETF2L public API

        Args:
            match_data (dict): data pulled from the ETF2L API (or in the same format)

        Returns:
            Match: A match object encapsulating the ETF2L match data passed in
        """

        # Get the match name if it exists
        match_name = (match_data.get("competition", {}).get("name", "") + f' {match_data.get("round", "")}').strip() or None

        # Find the IDs of the home and away teams
        home_team = match_data.get("clan1", {}).get("id", None)
        away_team = match_data.get("clan2", {}).get("id", None)

        # Initialise with as much data as can be taken
        match = Match(
            SiteID.etf2l_id(match_data["id"]),
            match_name,
            float(match_data.get("time", 0)) or None,
            match_data.get("defaultwin", None),
            SiteID.etf2l_id(match_data.get("competition", {}).get("id", None)),
            SiteID.etf2l_id(home_team),
            SiteID.etf2l_id(away_team)
        )

        # Add map data if it exists
        for map_ in match_data.get("map_results", []):
            match.add_map(TfDataDecoder.decode_map(TfSource.ETF2L, map_))

        return match

    @staticmethod
    def _decode_internal_match(match_data_: dict) -> Match:
        match_data = match_data_["match"]
        match = Match(
            match_data["matchId"],
            match_data.get("matchName", None),
            float(match_data.get("matchTime", None) or 0) or None,
            match_data.get("wasForfeit", None),
            match_data.get("event", None),
            match_data.get("homeTeam", None),
            match_data.get("awayTeam", None),
        )
        match.maps = match_data.get("maps", [])
        return match

    @staticmethod
    def decode_match(source: TfSource, match_data: dict) -> Match:
        func_ = getattr(TfDataDecoder, f"_decode_{source.name.lower()}_match")
        return func_(match_data)

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
    def decode_team(source: TfSource, team_data: dict) -> Team:
        func_ = getattr(TfDataDecoder, f"_decode_{source.name.lower()}_team")
        return func_(team_data)

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        """Overrided function for decoding data using json.load

        Args:
            obj (_type_): _description_

        Returns:
            _type_: _description_
        """
        if "source" in obj:
            return SiteID(int(obj["source"]["id"]), TfSource[obj["source"]["site"]])
        if "map" in obj:
            return TfDataDecoder.decode_map(TfSource.INTERNAL, obj)
        if "match" in obj:
            return TfDataDecoder.decode_match(TfSource.INTERNAL, obj)
        if "team" in obj:
            return TfDataDecoder.decode_team(TfSource.INTERNAL, obj)
        return obj

class TfDataEncoder(json.JSONEncoder):
    """Custom JSON encoder for writing TF2 data to json files
    """
    def default(self, o: Any) -> Any:

        # Encode Map
        if isinstance(o, (Map, SiteID, Match, Team)):
            return o.serialize()

        return super().default(o)
