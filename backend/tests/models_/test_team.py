from models import Team


def test_team_insert(session):
    t = Team()
    session.add(t)
    session.commit()
    assert Team.get(t.team_id) is not None

def test_team_ids(session):
    t = Team()
    assert t.team_id == 1
    new_team = Team()
    new_team_2 = Team()
    assert new_team.team_id == 2
    assert new_team_2.team_id == 3

    session.add_all([t, new_team])
    session.commit()

    assert Team.UNCOMMITTED_IDS == {3}
    session.add(new_team_2)
    session.commit()
    assert not Team.UNCOMMITTED_IDS
    assert Team().team_id == 4
