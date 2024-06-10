from services import MatchService
from utils import TempFile


def test_scrape_match_page():
  result = MatchService.scrape_match_page(0)

  assert len(result) == 1000
  assert int(result[0]) == 32
  assert int(result[-1]) == 1271

  result = MatchService.scrape_match_page(1e7)
  assert result == []

  result = MatchService.scrape_match_page(-500)
  assert result == []

def test_find_match_ids():
  f: TempFile
  # test subsequent calls
  with TempFile("tests\\test_data\\test_find_match_ids.json") as f:
    f.write([], json=True)

    MatchService.find_match_ids("tests\\test_data\\test_find_match_ids.json")
    length = len(f.read(json=True))

    MatchService.find_match_ids("tests\\test_data\\test_find_match_ids.json")
    new_data = f.read(json=True)

    assert len(new_data) == length
    assert MatchService.scrape_match_page(len(new_data)) == []


