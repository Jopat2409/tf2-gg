import json
import time
import requests
from multiprocessing import Pool
import services.teamservice as TeamService
import services.matchservice as MatchService
import services.playerservice as PlayerService


def read_or_create(file: str, default: dict = {}) -> None:
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(file, "w") as f:
            json.dump(default, f)
    return default

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


def update_all_services() -> None:
    """
    Updates all database tables from scraped data, may take a bit of time
    """
    pass
