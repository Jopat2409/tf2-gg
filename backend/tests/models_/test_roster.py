from models import Roster, Team
from utils.typing import SiteID

def test_constructor(session):
    roster = Roster(SiteID.rgl_id(32))
    assert roster.rgl_team_id == 32
    assert Roster.count() == 0

    roster = Roster(SiteID.rgl_id(32), 10)
    assert roster.rgl_team_id == 32
    assert roster.team_id == 10
    assert roster.team is not None
    assert roster.team.team_id == 10
    assert Team.count() == 0

def test_roster_stage(session):

    # Test roster with just roster ID
    roster_1 = Roster(SiteID.rgl_id(32))
    roster_1.stage(session)
    assert Roster.count() == 0
    session.commit()
    assert Roster.count() == 1
    assert Team.count() == 0
    assert Roster.get_fromsource(SiteID.rgl_id(32)) is not None
    roster_1.stage(session)
    assert Roster.count() == 1

    # Test roster with new team
    roster_2 = Roster(SiteID.rgl_id(40), 10)
    roster_2.stage(session)
    assert Roster.count() == 1
    assert Team.count() == 0
    session.commit()
    assert Roster.count() == 2
    assert Team.count() == 1
    assert Roster.get_fromsource(SiteID.rgl_id(40)) is not None
    assert Team.get(10) is not None
    session.commit()

    # Test roster with already created team
    roster_3 = Roster(SiteID.rgl_id(50), 10)
    roster_3.stage(session)
    assert Roster.count() == 2
    assert Team.count() == 1
    session.commit()
    assert Roster.count() == 3
    assert Team.count() == 1

    # Test roster with 2
    roster_4 = Roster(SiteID.rgl_id(60), 20)
    roster_5 = Roster(SiteID.rgl_id(70), 20)
    roster_4.stage(session)
    roster_5.stage(session)
    session.commit()
    assert Team.count() == 2
    assert Roster.count() == 5

def test_roster_insert(session):
    pass
