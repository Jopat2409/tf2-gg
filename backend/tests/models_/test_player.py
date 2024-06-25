import pytest

from db.player import Player, insert_player, get_player, update_player

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
