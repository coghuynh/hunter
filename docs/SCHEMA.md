Graph Schema and Validation
===========================

Overview
- Centralized enums `NodeLabel`, `RelType` in `src/hunter/domains/types.py`.
- Schema registry and validators in `src/hunter/domains/schema.py`.
- Concrete node and relationship Pydantic models in `src/hunter/domains/nodes.py` and `src/hunter/domains/relationships.py`.
- Safe Cypher helpers in `src/hunter/utils/cypher_builder.py`.

Quick Validation
- Node: `SCHEMA.validate_node_props(NodeLabel.Candidate, {"name": "alice"})`
- Relationship: `SCHEMA.validate_relationship(RelType.HAS_SKILL, NodeLabel.Candidate, NodeLabel.Skill, {"level": 3})`

Safe Builders
- `build_merge_node(NodeLabel.Skill, {"name": "python"}, merge_on=["name"])` -> `(cypher, params)`
- `build_link(NodeLabel.Candidate, RelType.HAS_SKILL, NodeLabel.Skill, start_uid, end_uid, {"level": 3})`

Neo4j Constraints
- Apply idempotent constraints: `from hunter.db.constraints import apply_constraints; apply_constraints()`

Integrating in Repositories
- Repos now call schema validators before executing Cypher.
- Prefer using enums over raw strings for labels/rel types.

