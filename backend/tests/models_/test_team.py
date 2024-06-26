import time
import pytest

from db.team import Team, insert_team, get_team, update_team, get_roster_id, insert_teams
from db.player import Player, get_player, get_current_teams, get_teams

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

def test_team_player_operations():

    # invaild player id
    assert get_current_teams(-100) == get_teams(-100) == []

    # valid player id but no teams
    assert get_current_teams(76561197970669109) == get_teams(76561197970669109) == []

    # Valid teams
    current_teams = get_current_teams(122345)
    assert len(current_teams) == 1
    assert current_teams[0].team_id == SiteID.rgl_id(32)

def test_insert_teams():

    assert insert_teams([Team(SiteID.rgl_id(x)) for x in range(20000, 21000)])

    for i in range(20000, 21000):
        assert get_team(SiteID.rgl_id(i))

def test_timeit_insert():
    test_teams_1 = [Team(SiteID.rgl_id(x)) for x in range(4000, 5000)]
    test_teams_2 = [Team(SiteID.rgl_id(x)) for x in range(6000, 7000)]

    t = time.perf_counter_ns()
    insert_teams(test_teams_1)
    avg_teams = (time.perf_counter_ns() - t) / 1e3
    print(f"Average for bulk: {avg_teams}")

    t = time.perf_counter_ns()
    for x in test_teams_2:
        insert_team(x)
    avg_team = (time.perf_counter_ns() - t) / 1e3
    print(f"Average for non bulk: {avg_team}")

    assert 1 == 0
