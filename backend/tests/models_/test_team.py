import pytest

from db.team import Team, insert_team, get_team, update_team, get_roster_id
from db.player import Player, get_player

from utils.typing import SiteID

def test_team_constructor():

    assert Team(SiteID.rgl_id(40)).team_id == SiteID.rgl_id(40)

    with pytest.raises(ValueError):
        Team(10)

def test_team_methods():

    team = Team(SiteID.rgl_id(10))
    team.add_player(12345, 190, 200)
    assert team.players[0]["joinedAt"] == 190.0
    assert team.players[0]["leftAt"] == 200.0

def test_db_operations():
    froyotech = Team(
        SiteID.rgl_id(41),
        "froyotech",
        "FROYO",
        1234567,
        1234566
    )

    assert insert_team(froyotech)
    assert not insert_team(froyotech)

    assert get_team(1) == froyotech
    assert get_team(SiteID.rgl_id(41)) == froyotech

    assert get_roster_id(SiteID.rgl_id(41)) == 1

    g6 = Team(
        SiteID.rgl_id(32),
        "like a g6",
        "G6",
        1284798216,
        129847827,
        players=[{"steamId": 122345, "joinedAt": 9274981.0, "leftAt": None}]
    )

    assert insert_team(g6)
    assert get_team(2) == g6
    assert get_team(SiteID.rgl_id(32)) == g6
    assert get_player(122345) == Player(122345)

    g6.name = "like a g7 :o"
    g6.tag = "G7"
    g6.add_player(420, 123094123)

    assert update_team(g6)

    assert get_team(2) == g6
    assert len(get_team(2).players) == 2

    assert not update_team(Team(SiteID.rgl_id(12374)))
