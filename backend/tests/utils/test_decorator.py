from models import Team
import random

def test_cache_ids(session):
    # A bunch of non-committed
    ids = [Team() for _ in range(1000)]
    assert len(ids) == 1e3
    assert len(ids) == len(set([team.team_id for team in ids]))

    # Test inserts
    team1 = Team()
    team2 = Team()
    team3 = Team()

    session.add_all([team1, team3])
    session.commit()
    assert Team().team_id == 1004

    ids_2 = []
    for i in range(50):
        t = Team()
        ids_2.append(t.team_id)
        if random.random() < 0.5:
            session.add(t)
        if random.random() < 0.15:
            session.commit()
    assert len(ids_2) == 50
    assert len(ids_2) == len(set(ids_2))

def create_team():
    team = Team()

def test_cache_out_of_scope(session):
    # Check the ID is reset when Team goes out of scope
    assert Team.insert(session).team_id == 1
