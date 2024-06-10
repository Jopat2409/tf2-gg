from utils.scraping import TfDataDecoder, TfSource
from models import Match, MatchResult
import json

def test_tfdecoder_match(session):
  with open("tests\\test_data\\test.json", "r", encoding='utf-8') as f:
    rgl_match_data = json.load(f)["test_util_data"]["matches"]["32"]
  match = TfDataDecoder.decode_match(TfSource.RGL, rgl_match_data)

  assert isinstance(match, Match)
  assert match.match_epoch == 1497490200.0
  assert match.rgl_match_id == 32
  assert match.season_id == 1
  assert match.division_id == 7
  assert match.region_id == 1
  assert match.match_name == "Week 1 - Badwater"

  assert len(match.results) == 2
  assert match.results[0].map_name == "pl_badwater_pro_v9"
  assert match.results[0].score == 2
  assert match.results[1].score == 0

  # Check that calling decode does not commit anything to database
  assert len(Match.query.all()) == 0
  assert len(MatchResult.query.all()) == 0

  # Check that calling decode does not commit
  session.commit()
  assert len(Match.query.all()) == 0
  assert len(MatchResult.query.all()) == 0

  match_2 = TfDataDecoder.decode_match(TfSource.RGL, {"matchId": 10})
  assert isinstance(match_2, Match)
  assert match_2.rgl_match_id == 10
  assert match_2.match_epoch is None
