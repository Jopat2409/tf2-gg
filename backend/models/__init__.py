"""
All models fall into two categories: models that directly encapsulate things recieved from APIs (ApiModels) and things
that are purely internal (Models)

All models need:
    `__init__()` - constructor that performs no database operations, simply populates the data structure\n
    `get()` - a static method to get a model given the `internal ID`\n
    `stage()` - a method that ensures a given object's attributes have all been added to the database\n
    `insert()` - a method that takes in the attributes and directly inserts all data into the database\n
    `update()` - a static method that updates the stored row with the given data\n

ApiModels need:
    `get_fromsource()` - a method to get a model from the API ID

"""
from models.team import Team
from models.player import Player
from models.roster import Roster
from models.roster_player_a import RosterPlayerAssociation
from models.match_result import MatchResult
from models.match import Match
from models.season import Season


__all__ = [Team, Player, Roster, RosterPlayerAssociation, MatchResult, Match, Season]
