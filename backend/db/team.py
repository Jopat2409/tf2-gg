from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from flask import current_app as app
from db.database import query_db, insert_db

@dataclass
class Team:
    team_id: int

def insert(team: Team) -> None:
    result = insert_db("INSERT INTO teams (team_id) VALUES (?)", args=[int(team.team_id)])

def get(team_id: int) -> Optional[Team]:
    result = query_db("SELECT * FROM teams WHERE team_id = ?", args=[int(team_id)], one=True)
    print(f"Result: {result}")
    return result


if __name__ == "__main__":
    get(10)
