import pytest

import time

from db.player import Player, insert_player, get_player, update_player, insert_players

def test_player_constructor():
    b4nny = Player(76561197970669109)
    assert b4nny.steam_id == 76561197970669109

    b4nny = Player("76561197970669109")
    assert b4nny.steam_id == 76561197970669109

    with pytest.raises(TypeError):
        Player()

    with pytest.raises(ValueError):
        Player("hello")

def test_player_db_operations():

    b4nny = Player(76561197970669109, "B4NNY", "goofy.png", "Grant", "Vincent")
    assert insert_player(b4nny)

    assert get_player(b4nny.steam_id) == b4nny
    assert not insert_player(b4nny)

    b4nny.alias = "GURNEY"
    assert update_player(b4nny)
    assert get_player(b4nny.steam_id) == b4nny

    b4nny.steam_id += 1
    assert not update_player(b4nny)

def test_insert_players():

    assert insert_players([Player(x) for x in range(2345,2355)])
    for i in range(2345, 2355):
        assert get_player(i)

    assert insert_players([Player(x) for x in range(2340, 2350)])
    assert not insert_players([Player(x) for x in range(2340, 2355)])

def test_timeit():
    test_players_1 = [Player(x) for x in range(4000, 5000)]
    test_players_2 = [Player(x) for x in range(6000, 7000)]

    t = time.perf_counter_ns()
    insert_players(test_players_1)
    avg_players = (time.perf_counter_ns() - t) / 1e3

    t = time.perf_counter_ns()
    for x in test_players_2:
        insert_player(x)
    avg_player = (time.perf_counter_ns() - t) / 1e3

    assert avg_players < avg_player
