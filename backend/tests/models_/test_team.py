from models import Team

def test_team_constructor(session):

    team_1 = Team()
    assert Team.count() == 0

    team_2 = Team(10)
    assert team_2.team_id == 10
    assert Team.count() == 0

    del team_1

    assert not Team._CACHEIDS_UNCOMMITTED_IDS
    assert not Team._STAGEDMODEL_STAGED_OBJECTS

def test_team_stage(session):
    # Normal stage
    t = Team()
    t.stage(session)
    assert Team.count() == 0
    session.commit()
    assert Team.count() == 1

    # Staging a team with a team ID that already exists simply does nothing
    t_2 = Team(t.team_id)
    t_2.stage(session)
    session.commit()
    assert Team.count() == 1

    # Test not insert with double stage before commit
    team_3 = Team(1234)
    team_4 = Team(1234)
    team_3.stage(session)
    team_4.stage(session)
    session.commit()
    assert Team.count() == 2

def test_team_insert(session):

    # Standard insert
    print(f"IDS: {Team._CACHEIDS_UNCOMMITTED_IDS}")
    print(f"STAGED: {Team._STAGEDMODEL_STAGED_OBJECTS}")
    team = Team.insert(session)
    print(team.team_id)
    assert Team.get(team.team_id).team_id == 1

    # Insert without commit
    team_2 = Team.insert(session, commit=False)
    assert team_2.team_id == 2
    assert Team.get(team_2.team_id) is None
    session.commit()
    assert Team.get(team_2.team_id).team_id == 2

    assert Team.insert(session, 1) is None


def test_get_or_insert(session):
    Team.insert(session, 1)

    assert Team.get_or_insert(1, session).team_id == 1
    assert Team.count() == 1

    assert Team.get_or_insert(2, session).team_id == 2
    assert Team.get(2) is not None
    assert Team.count() == 2
