from __future__ import annotations
from typing import List

from hunter.db import run as _run


CONSTRAINTS: List[str] = [
    # Candidate
    "CREATE CONSTRAINT candidate_uid IF NOT EXISTS FOR (c:Candidate) REQUIRE c.uid IS UNIQUE",
    # Dictionary nodes unique keys
    "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (n:Skill) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT project_name IF NOT EXISTS FOR (n:Project) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT language_name IF NOT EXISTS FOR (n:Language) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT major_name IF NOT EXISTS FOR (n:Major) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT university_name IF NOT EXISTS FOR (n:University) REQUIRE n.name IS UNIQUE",
    "CREATE CONSTRAINT job_title_title IF NOT EXISTS FOR (n:JobTitle) REQUIRE n.title IS UNIQUE",
]


def apply_constraints() -> None:
    for q in CONSTRAINTS:
        _run(q, {})

