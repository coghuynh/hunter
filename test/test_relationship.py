import os
import time
from datetime import datetime

import pytest
from neomodel import config

from hunter.db import db_instance as db
from hunter.repository.feature_repo import (
    SkillManagement,
    ProjectManagement,
    LanguageManagement,
    JobTitleManagement,
    MajorManagement,
    UniversityManagement,
)

# -----------------------------
# Global/Session-level fixtures
# -----------------------------

@pytest.fixture(scope="session", autouse=True)
def configure_neo4j():
    """
    Configure Neo4j connection for test session and ensure a clean DB
    before and after all tests.
    """
    # Allow .env to override if present
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "test20032004")

    if uri.startswith("bolt://") or uri.startswith("bolt+s://"):
        scheme, rest = uri.split("://", 1)
        database_url = f"{scheme}://{user}:{pwd}@{rest}"
    else:
        database_url = f"bolt://{user}:{pwd}@localhost:7687"

    config.DATABASE_URL = database_url
    # small delay to make sure config is set (mostly useful in CI)
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


# -----------------------------
# Helpers
# -----------------------------

def _mk_candidate(uid: str):
    db.cypher_query(
        """
        MERGE (c:Candidate {uid: $uid})
        ON CREATE SET c.created_at = datetime()
        """,
        {"uid": uid},
    )


# -----------------------------
# Smoke list for dict entities
# -----------------------------

DICT_ENTITIES = [
    (SkillManagement, "name", "Python", "Python Advanced"),
    (ProjectManagement, "name", "Alpha", "AlphaX"),
    (LanguageManagement, "name", "Vietnamese", "Vietnamese Pro"),
    (JobTitleManagement, "title", "Data Scientist", "Senior Data Scientist"),
    (MajorManagement, "name", "AI", "CS"),
    (UniversityManagement, "name", "VNU-UET", "HUST"),
]


# -----------------------------
# Tests
# -----------------------------

@pytest.mark.parametrize("Repo,key,new_name,updated_name", DICT_ENTITIES)
def test_upsert_get_getlist_delete_roundtrip(Repo, key, new_name, updated_name):
    # upsert by name
    uid = Repo.upsert(new_name)
    assert isinstance(uid, str) and len(uid) > 0

    # get_by_name
    got = Repo.get_by_name(new_name)
    assert got and got["uid"] == uid and got[key] == new_name

    # get_by_uids
    got_list = Repo.get_by_uids([uid])
    assert isinstance(got_list, list) and got_list and got_list[0]["uid"] == uid

    # get_list (pagination existence)
    page = Repo.get_list(skip=0, limit=10)
    assert any(row["uid"] == uid for row in page)

    # upsert with given uid -> update name/title
    uid_again = Repo.upsert(updated_name, uid=uid)
    assert uid_again == uid
    got2 = Repo.get_by_name(updated_name)
    assert got2 and got2["uid"] == uid and got2[key] == updated_name

    # delete
    deleted = Repo.delete(uid)
    assert deleted == 1
    assert Repo.get_by_name(updated_name) is None


def test_link_by_name_and_list_for_candidate_includes_rel_props():
    cand_uid = "cand-001"
    _mk_candidate(cand_uid)

    rel_eid = SkillManagement.link_by_name(
        cand_uid,
        "Python",
        # Schema for HAS_SKILL allows level:int, years:float, weight:float
        rel_props={"weight": 0.9, "level": 4, "years": 2.0},
    )
    assert isinstance(rel_eid, str) and len(rel_eid) > 0

    rows = SkillManagement.list_for_candidate(cand_uid)
    assert len(rows) == 1
    row = rows[0]
    # basic fields
    assert row["rel_eid"] == rel_eid
    assert row["name"] == "Python"
    # rel props are flattened and prefixed with rel_
    assert row.get("rel_weight") == 0.9
    assert row.get("rel_level") == 4
    assert float(row.get("rel_years")) == 2.0


def test_link_by_uids_update_props_and_unlink_by_uids():
    cand_uid = "cand-002"
    _mk_candidate(cand_uid)

    # create feature, link by uids
    skill_uid = SkillManagement.upsert("NumPy")
    rel_eid_1 = SkillManagement.link_by_uids(
        cand_uid, skill_uid, rel_props={"weight": 0.5}
    )
    assert rel_eid_1

    # update same relationship props (r += rel_props should update)
    rel_eid_2 = SkillManagement.link_by_uids(
        cand_uid, skill_uid, rel_props={"weight": 0.8, "years": 3.0}
    )
    assert rel_eid_2 == rel_eid_1

    rows = SkillManagement.list_for_candidate(cand_uid)
    assert len(rows) == 1
    row = rows[0]
    assert row.get("rel_weight") == 0.8
    assert float(row.get("rel_years")) == 3.0

    # unlink
    deleted = SkillManagement.unlink_by_uids(cand_uid, skill_uid)
    assert deleted == 1
    assert SkillManagement.list_for_candidate(cand_uid) == []


def test_unlink_all_for_candidate_by_type_only():
    cand_uid = "cand-003"
    _mk_candidate(cand_uid)

    # two skills + one language
    s1 = SkillManagement.upsert("PyTorch")
    s2 = SkillManagement.upsert("HIP")
    l1 = LanguageManagement.upsert("English")

    SkillManagement.link_by_uids(cand_uid, s1)
    SkillManagement.link_by_uids(cand_uid, s2)
    LanguageManagement.link_by_uids(cand_uid, l1)

    # only remove skills
    cnt = SkillManagement.unlink_all_for_candidate(cand_uid)
    assert cnt == 2

    # verify skills removed, language remains
    assert SkillManagement.list_for_candidate(cand_uid) == []
    langs = LanguageManagement.list_for_candidate(cand_uid)
    assert len(langs) == 1 and langs[0]["name"] == "English"


def test_delete_feature_detaches_relationships():
    cand_uid = "cand-004"
    _mk_candidate(cand_uid)

    uni_uid = UniversityManagement.upsert("HUST")
    rel_eid = UniversityManagement.link_by_uids(cand_uid, uni_uid)
    assert rel_eid

    # deleting the feature node should detach rels (DETACH DELETE)
    deleted = UniversityManagement.delete(uni_uid)
    assert deleted == 1

    # no relationships should remain
    rows = UniversityManagement.list_for_candidate(cand_uid)
    assert rows == []
