

import os
import math
import time
import pytest

from dotenv import load_dotenv, find_dotenv

from neomodel import db, config


from hunter.repository.candidate_repo import (
    upsert_candidate,
    get_candidate_by_uid,
    list_candidates,
    delete_candidate,
    attach_job_titles,
    attach_skills,
    attach_languages,
    attach_education,
    attach_projects,
    get_candidate_neighbors,
)

load_dotenv(find_dotenv(".env", usecwd=True), override=False)


# -------------------------------
# Test setup / fixtures
# -------------------------------

@pytest.fixture(scope="session", autouse=True)
def configure_neo4j():
    """Configure neomodel connection from env once per test session.

    Expected env (examples):
      NEO4J_URI=bolt://localhost:7687
      NEO4J_USER=neo4j
      NEO4J_PASS=pass
    We build neomodel DATABASE_URL = bolt://user:pass@host:port
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "test")

    # Build DATABASE_URL
    if uri.startswith("bolt://") or uri.startswith("bolt+s://"):
        scheme, rest = uri.split("://", 1)
        database_url = f"{scheme}://{user}:{pwd}@{rest}"
    else:
        database_url = f"bolt://{user}:{pwd}@localhost:7687"
        # print(database_url)

    config.DATABASE_URL = database_url
    time.sleep(0.2)

    # Ensure a clean DB before session
    db.cypher_query("MATCH (n) DETACH DELETE n")

    yield

    # Cleanup after session
    db.cypher_query("MATCH (n) DETACH DELETE n")


@pytest.fixture(autouse=True)
def clean_between_tests():
    """Clean DB between tests for isolation."""
    db.cypher_query("MATCH (n) DETACH DELETE n")
    yield
    db.cypher_query("MATCH (n) DETACH DELETE n")


# -------------------------------
# Helper
# -------------------------------

def approx(a: float, b: float, tol: float = 1e-6):
    return abs(a - b) <= tol


# -------------------------------
# Tests
# -------------------------------

def test_upsert_and_get_candidate():
    uid = upsert_candidate(name="Alice", location="HCMC")
    got = get_candidate_by_uid(uid)
    assert got is not None
    assert got["name"] == "Alice"
    assert got["location"] == "HCMC"

    # Update via uid path
    uid2 = upsert_candidate(name="Alice Updated", location="Saigon", uid=uid)
    assert uid2 == uid
    got2 = get_candidate_by_uid(uid)
    assert got2["name"] == "Alice Updated"
    assert got2["location"] == "Saigon"


def test_list_and_delete_candidates():
    u1 = upsert_candidate("Bob")
    u2 = upsert_candidate("Carol")

    lst = list_candidates()
    names = {c["name"] for c in lst}
    assert {"Bob", "Carol"}.issubset(names)

    assert delete_candidate(u1) == 1
    assert get_candidate_by_uid(u1) is None or get_candidate_by_uid(u1) == {}



