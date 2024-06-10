from models import Match, MatchResult, Roster
import json
from utils.typing import SiteID, TfSource
from utils.scraping import TfDataDecoder

def test_insert(session):
    m_1 = SiteID.rgl_id(10)
    success = Match.insert(session, m_1)
    assert success
    assert Match.get_fromsource(m_1).rgl_match_id == 10

    m_1 = SiteID.rgl_id(10)
    success = Match.insert(session, m_1, commit=False)
    assert not success

    m_2 = SiteID.rgl_id(15)
    success = Match.insert(session, m_2, commit=False)
    assert not Match.get_fromsource(m_2)
    session.commit()
    assert Match.get_fromsource(m_2).rgl_match_id == 15

def test_get_or_insert(session):
    assert Match.get_or_insert(session, SiteID.rgl_id(10)).rgl_match_id == 10
    assert Match.get_or_insert(session, SiteID.rgl_id(10)).rgl_match_id == 10
    assert Match.get_or_insert(session, SiteID.rgl_id(15), commit=False).rgl_match_id == 15
    assert not Match.get_fromsource(SiteID.rgl_id(15))
    session.commit()
    assert Match.get_fromsource(SiteID.rgl_id(15)).rgl_match_id == 15

def test_get_source(session):
    m_1 = SiteID.rgl_id(10)
    assert Match.insert(session, m_1)
    assert Match.get_fromsource(m_1).get_site_id() == m_1

    m_2 = SiteID.rgl_id(15)
    match = Match.insert(session, m_2, commit=False)
    assert match.get_site_id() == m_2

def test_update(session):
    m_1 = SiteID.rgl_id(10)
    assert Match.insert(session, m_1)
    assert Match.get_fromsource(m_1).rgl_match_id == 10

    to_update = Match.get_fromsource(m_1)
    to_update.match_epoch = 10
    to_update.division_id = 7
    assert Match.update(session, to_update)
    assert Match.get_fromsource(m_1).match_epoch == 10
    assert Match.get_fromsource(m_1).division_id == 7

    m_2 = SiteID.rgl_id(32)
    assert Match.insert(session, m_2)
    with open("tests\\test_data\\test.json", "r", encoding='utf-8') as f:
        rgl_match_data = json.load(f)["test_util_data"]["matches"]["32"]

    match_2_update = TfDataDecoder.decode_match(TfSource.RGL, rgl_match_data)
    match_2_update.is_complete = True
    Match.update(session, match_2_update)

    assert len(MatchResult.query.all()) == 2
    assert len(Roster.query.all()) == 2

    match_2 = Match.get_fromsource(m_2)
    assert match_2.match_epoch == 1497490200.0
    assert match_2.rgl_match_id == 32
    assert match_2.season_id == 1
    assert match_2.division_id == 7
    assert match_2.region_id == 1
    assert match_2.match_name == "Week 1 - Badwater"

    assert len(match_2.results) == 2
    assert match_2.results[0].roster_id == 1
    assert match_2.results[0].map_name == "pl_badwater_pro_v9"
    assert match_2.results[0].score == 2
    assert match_2.results[1].score == 0

    assert match_2.is_complete == 1
    assert Match.get_incomplete(TfSource.RGL) == []
    print(Match.get_matches(54))
    assert Match.get_matches(54) == []
