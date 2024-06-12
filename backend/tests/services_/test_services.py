from services import scrape_parallel, sleep_then_request, get_first
import time


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

