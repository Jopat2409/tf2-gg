from models import Roster
from utils.typing import SiteID

def test_insert(session):
  # Insert single
  success = Roster.insert(session, SiteID.rgl_id(10))
  assert success
  assert not Roster.insert(session, SiteID.rgl_id(10))
  assert Roster.get_fromsource(SiteID.rgl_id(10))

  # Insert single (without commit)
  assert Roster.insert(session, SiteID.rgl_id(20), commit=False)
  assert not Roster.get_fromsource(SiteID.rgl_id(20))
  session.commit()
  assert Roster.get_fromsource(SiteID.rgl_id(20))

  # Insert single (recursive)
  success = Roster.insert(session, SiteID.rgl_id(30), recursive=True)
  assert success
  assert Roster.get_fromsource(SiteID.rgl_id(30)).team_id == 1

  # Insert single (related roster)
  success = Roster.insert(session, SiteID.rgl_id(35), recursive=True, related_rosters=[SiteID.rgl_id(30)])
  assert success
  assert Roster.get_fromsource(SiteID.rgl_id(35)).team_id == 1

  # Insert single (post-team-creation)
  success = Roster.insert(session, SiteID.rgl_id(40))
  assert success
  assert not Roster.get_fromsource(SiteID.rgl_id(40)).team_id

  # Insert recursive without commit
  success = Roster.insert(session, SiteID.rgl_id(45), recursive=True, commit=False)
  assert success
  session.commit()
  assert Roster.get_fromsource(SiteID.rgl_id(45)).team_id == 2
  # Test inserting just ID

  # Test inserting whole thing with linked stuff

  # test inserting epic epic carpal tunner
