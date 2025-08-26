import pytest

import os
from dotenv import load_dotenv, find_dotenv

# from hunter.repository.feature_repo import *
from hunter.db import db_instance as db
from neomodel import config
import time

load_dotenv(find_dotenv(".env", usecwd=True), override=False)

@pytest.fixture(scope="session", autouse=True)
def configure_neo4j():
    """
    Configure NEO4j
    """
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "test20032004")


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
    db.cypher_query("MATCH (n) DETACH DELETE n")
    yield
    db.cypher_query("MATCH (n) DETACH DELETE n")
    
    
# tests/test_feature_repo.py

import pytest

from hunter.repository.feature_repo import (
    SkillManagement,
    ProjectManagement,
    LanguageManagement,
    JobTitleManagement,
    MajorManagement,
    UniversityManagement
)

# ---------------------------
# Generic dictionary entities
# ---------------------------

DICT_ENTITIES = [
    (SkillManagement, "name", "Python", "Python Advanced"),
    (ProjectManagement, "name", "Alpha", "AlphaX"),
    (LanguageManagement, "name", "Vietnamese", "Vietnamese Pro"),
    (JobTitleManagement, "title", "Data Scientist", "Senior Data Scientist"),
    (MajorManagement, "name", "AI", "CS"),
    (UniversityManagement, "name", "VNU-UET", "HUST")
]


@pytest.mark.parametrize("Repo,key,initial,updated", DICT_ENTITIES)
def test_dict_repo_upsert_and_get_by_name(Repo, key, initial, updated):
    # upsert (no uid) — merge by unique key
    uid = Repo.upsert(initial)
    assert isinstance(uid, str) and len(uid) > 0

    # get_by_name
    obj = Repo.get_by_name(initial)
    assert obj is not None
    assert obj["uid"] == uid
    assert obj[key] == initial

    # upsert again (same key) returns same uid (merge on key)
    uid_again = Repo.upsert(initial)
    assert uid_again == uid

    # upsert with uid — update key field
    uid_updated = Repo.upsert(updated, uid=uid)
    assert uid_updated == uid

    # get_by_name(new key) points to same uid
    obj2 = Repo.get_by_name(updated)
    assert obj2 is not None
    assert obj2["uid"] == uid
    assert obj2[key] == updated

    # old key should not be found anymore (exact match)
    obj_old = Repo.get_by_name(initial)
    assert obj_old is None


@pytest.mark.parametrize("Repo,key,initial,_updated", DICT_ENTITIES)
def test_dict_repo_get_by_uids_and_list_and_delete(Repo, key, initial, _updated):
    # create multiple
    uids = [Repo.upsert(f"{initial} {i}") for i in range(5)]
    assert len(set(uids)) == 5

    # get_list first page
    page = Repo.get_list(skip=0, limit=3)
    assert len(page) == 3
    # verify schema
    for item in page:
        assert "uid" in item and key in item

    # get_list second page
    page2 = Repo.get_list(skip=3, limit=3)
    assert len(page2) in (2, 3)  # 2 left (total 5), but keep generic

    # get_by_uids
    got = Repo.get_by_uids(uids[:3])
    assert len(got) == 3
    got_uids = {g["uid"] for g in got}
    assert got_uids == set(uids[:3])

    # delete one
    del_count = Repo.delete(uids[0])
    assert del_count == 1

    # deleted should not appear
    obj = Repo.get_by_uids([uids[0]])
    assert obj == []

    # delete non-existing is idempotent-ish (returns 0)
    del_again = Repo.delete(uids[0])
    assert del_again == 0


@pytest.mark.parametrize("Repo,key,initial,_updated", DICT_ENTITIES)
def test_dict_repo_trims_input(Repo, key, initial, _updated):
    uid = Repo.upsert(f"  {initial}  ")
    obj = Repo.get_by_name(initial)  # exact trimmed name
    assert obj is not None
    assert obj["uid"] == uid
    assert obj[key] == initial


    

