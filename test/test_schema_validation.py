import pytest

from hunter.domains.schema import SCHEMA, GraphSchemaError
from hunter.domains.types import NodeLabel, RelType


def test_candidate_props_valid():
    SCHEMA.validate_node_props(NodeLabel.Candidate, {"name": "Alice", "location": "HCMC"})


def test_candidate_props_unknown_raises():
    with pytest.raises(GraphSchemaError):
        SCHEMA.validate_node_props(NodeLabel.Candidate, {"name": "Alice", "bogus": 1})


def test_skill_unique_name_present():
    SCHEMA.validate_node_props(NodeLabel.Skill, {"name": "python"})


def test_rel_has_skill_valid():
    SCHEMA.validate_relationship(
        RelType.HAS_SKILL,
        NodeLabel.Candidate,
        NodeLabel.Skill,
        {"level": 3, "years": 5.0},
    )


def test_rel_has_skill_wrong_end_raises():
    with pytest.raises(GraphSchemaError):
        SCHEMA.validate_relationship(
            RelType.HAS_SKILL,
            NodeLabel.Candidate,
            NodeLabel.Project,
            {},
        )

