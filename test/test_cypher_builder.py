import os
import time
from typing import Dict, Any

import pytest
from neomodel import config

from hunter.db import db_instance as db
from hunter.utils.cypher_builder import (
    build_merge_node,
    build_link,
    validate_node,
    validate_relationship,
)
from hunter.domains.types import NodeLabel, RelType
from hunter.domains.schema import GraphSchemaError


# -----------------------------
# Global/Session-level fixtures
# -----------------------------

@pytest.fixture(scope="session", autouse=True)
def configure_neo4j():
    """
    Configure Neo4j connection for test session and ensure a clean DB
    before and after all tests.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "test20032004")

    if uri.startswith("bolt://") or uri.startswith("bolt+s://"):
        scheme, rest = uri.split("://", 1)
        database_url = f"{scheme}://{user}:{pwd}@{rest}"
    else:
        database_url = f"bolt://{user}:{pwd}@localhost:7687"

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


# -----------------------------
# Helpers
# -----------------------------

def _run(q: str, params: Dict[str, Any]):
    rows, _ = db.cypher_query(q, params)
    return rows


# -----------------------------
# Tests for build_merge_node
# -----------------------------

def test_merge_node_by_unique_key_returns_same_uid():
    # Skill has unique key on name
    q1, p1 = build_merge_node(NodeLabel.Skill, {"name": "Python"}, merge_on=["name"], return_field="uid")
    r1 = _run(q1, p1)
    uid1 = r1[0][0]
    assert isinstance(uid1, str) and uid1

    # merge again with same name -> same uid
    q2, p2 = build_merge_node(NodeLabel.Skill, {"name": "Python"}, merge_on=["name"], return_field="uid")
    r2 = _run(q2, p2)
    uid2 = r2[0][0]
    assert uid2 == uid1


def test_merge_node_by_uid_sets_name_and_updates():
    # First create a Language by key
    q1, p1 = build_merge_node(NodeLabel.Language, {"name": "English"}, merge_on=["name"], return_field="uid")
    uid = _run(q1, p1)[0][0]
    assert uid

    # Now ensure MERGE by uid updates the name
    q2, p2 = build_merge_node(
        NodeLabel.Language,
        {"uid": uid, "name": "English Pro"},
        merge_on=["uid"],
        return_field="uid",
    )
    uid_again = _run(q2, p2)[0][0]
    assert uid_again == uid

    got, _ = db.cypher_query("MATCH (n:Language {uid:$u}) RETURN n.name", {"u": uid})
    assert got[0][0] == "English Pro"


def test_merge_node_unknown_prop_raises():
    with pytest.raises(GraphSchemaError):
        # Skill only allows {uid?, name}
        build_merge_node(NodeLabel.Skill, {"name": "X", "bogus": 1}, merge_on=["name"])  # type: ignore[arg-type]


# -----------------------------
# Tests for build_link
# -----------------------------

def test_build_link_sets_props_and_returns_eid():
    # Create candidate and skill
    cq, cp = build_merge_node(NodeLabel.Candidate, {"name": "Alice"}, merge_on=["name"], return_field="uid")
    cand_uid = _run(cq, cp)[0][0]
    sq, sp = build_merge_node(NodeLabel.Skill, {"name": "NumPy"}, merge_on=["name"], return_field="uid")
    skill_uid = _run(sq, sp)[0][0]

    # Link with properties as per schema
    lq, lp = build_link(
        NodeLabel.Candidate,
        RelType.HAS_SKILL,
        NodeLabel.Skill,
        start_uid=cand_uid,
        end_uid=skill_uid,
        rel_props={"level": 3, "years": 4.0, "weight": 0.8},
        return_field="eid",
    )
    eid = _run(lq, lp)[0][0]
    assert isinstance(eid, str) and eid

    rows, _ = db.cypher_query(
        """
        MATCH (:Candidate {uid:$c})-[r:HAS_SKILL]->(:Skill {uid:$s})
        RETURN r.level, r.years, r.weight, r.eid
        """,
        {"c": cand_uid, "s": skill_uid},
    )
    assert rows and rows[0][0] == 3 and float(rows[0][1]) == 4.0 and float(rows[0][2]) == 0.8 and rows[0][3] == eid


def test_validate_helpers_work():
    # Node validation ok
    validate_node(NodeLabel.Project, {"name": "Alpha"})
    # Relationship validation ok
    validate_relationship(RelType.WORKED_ON, NodeLabel.Candidate, NodeLabel.Project, {})
    # Relationship wrong labels
    with pytest.raises(GraphSchemaError):
        validate_relationship(RelType.WORKED_ON, NodeLabel.Candidate, NodeLabel.Skill, {})

