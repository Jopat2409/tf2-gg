from services import TeamService, MatchService
from utils.typing import SiteID

def test_get_rgl_teams():
    assert TeamService.get_rgl_teams_from_matches(MatchService.scrape_rgl_matches([32])) == [SiteID.rgl_id(41), SiteID.rgl_id(54)]

def test_scrape_rgl_teams():
    pass