from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple, Type

from .types import NodeLabel, RelType


class GraphSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class PropertySpec:
    name: str
    py_type: Tuple[Type, ...] = (str,)
    required: bool = False


@dataclass(frozen=True)
class NodeSchema:
    label: NodeLabel
    properties: Mapping[str, PropertySpec]
    unique_keys: Tuple[str, ...] = field(default_factory=tuple)

    def validate_props(self, props: Mapping[str, Any]) -> None:
        allowed = set(self.properties.keys())
        unknown = [k for k in props.keys() if k not in allowed]
        if unknown:
            raise GraphSchemaError(
                f"Unknown properties for {self.label}: {', '.join(unknown)}"
            )

        missing = [name for name, spec in self.properties.items() if spec.required and name not in props]
        if missing:
            raise GraphSchemaError(
                f"Missing required properties for {self.label}: {', '.join(missing)}"
            )

        for k, v in props.items():
            if v is None:
                continue
            spec = self.properties[k]
            if not isinstance(v, spec.py_type):
                raise GraphSchemaError(
                    f"Property {self.label}.{k} expects {spec.py_type} but got {type(v)}"
                )


@dataclass(frozen=True)
class RelationshipSchema:
    rel_type: RelType
    start_label: NodeLabel
    end_label: NodeLabel
    properties: Mapping[str, PropertySpec] = field(default_factory=dict)

    def validate(self, start_label: NodeLabel, end_label: NodeLabel, props: Mapping[str, Any]) -> None:
        if start_label != self.start_label or end_label != self.end_label:
            raise GraphSchemaError(
                f"Relationship {self.rel_type} requires ({self.start_label})-[]->({self.end_label}),"
                f" got ({start_label})-[]->({end_label})"
            )
        allowed = set(self.properties.keys())
        unknown = [k for k in props.keys() if k not in allowed]
        if unknown:
            raise GraphSchemaError(
                f"Unknown properties for {self.rel_type}: {', '.join(unknown)}"
            )
        for k, v in props.items():
            if v is None:
                continue
            spec = self.properties[k]
            if not isinstance(v, spec.py_type):
                raise GraphSchemaError(
                    f"Property {self.rel_type}.{k} expects {spec.py_type} but got {type(v)}"
                )


class GraphSchema:
    def __init__(self) -> None:
        self._nodes: Dict[NodeLabel, NodeSchema] = {}
        self._rels: Dict[RelType, RelationshipSchema] = {}

    # ---- Registration ----
    def add_node(self, schema: NodeSchema) -> None:
        self._nodes[schema.label] = schema

    def add_relationship(self, schema: RelationshipSchema) -> None:
        self._rels[schema.rel_type] = schema

    # ---- Lookups ----
    def node(self, label: NodeLabel) -> NodeSchema:
        if label not in self._nodes:
            raise GraphSchemaError(f"Unknown node label: {label}")
        return self._nodes[label]

    def relationship(self, rel_type: RelType) -> RelationshipSchema:
        if rel_type not in self._rels:
            raise GraphSchemaError(f"Unknown relationship type: {rel_type}")
        return self._rels[rel_type]

    # ---- Validation helpers ----
    def validate_node_props(self, label: NodeLabel, props: Mapping[str, Any]) -> None:
        self.node(label).validate_props(props)

    def validate_relationship(
        self,
        rel_type: RelType,
        start_label: NodeLabel,
        end_label: NodeLabel,
        props: Mapping[str, Any],
    ) -> None:
        self.relationship(rel_type).validate(start_label, end_label, props)


def default_schema() -> GraphSchema:
    """Define the default graph schema for this project."""
    s = GraphSchema()

    # Common properties
    uid = PropertySpec("uid", (str,), required=False)
    name = PropertySpec("name", (str,), required=True)
    title = PropertySpec("title", (str,), required=True)
    created_at = PropertySpec("created_at", (str,), required=False)  # Neo4j datetime string on return
    updated_at = PropertySpec("updated_at", (str,), required=False)

    # Candidate
    s.add_node(
        NodeSchema(
            label=NodeLabel.Candidate,
            properties={
                "uid": uid,
                "name": name,
                "location": PropertySpec("location", (str,), required=False),
                "headline": PropertySpec("headline", (str,), required=False),
                "remote_ok": PropertySpec("remote_ok", (bool,), required=False),
                "experience_years": PropertySpec("experience_years", (int, float), required=False),
                # salary flattened
                "salary_currency": PropertySpec("salary_currency", (str,), required=False),
                "salary_min": PropertySpec("salary_min", (int, float), required=False),
                "salary_max": PropertySpec("salary_max", (int, float), required=False),
                "created_at": created_at,
                "updated_at": updated_at,
            },
            unique_keys=("uid",),
        )
    )

    # Dictionary-like nodes
    dict_common = {"uid": uid, "created_at": created_at, "updated_at": updated_at}

    s.add_node(
        NodeSchema(NodeLabel.Skill, properties={**dict_common, "name": name}, unique_keys=("name",))
    )
    s.add_node(
        NodeSchema(NodeLabel.Project, properties={**dict_common, "name": name}, unique_keys=("name",))
    )
    s.add_node(
        NodeSchema(NodeLabel.Language, properties={**dict_common, "name": name}, unique_keys=("name",))
    )
    s.add_node(
        NodeSchema(NodeLabel.JobTitle, properties={**dict_common, "title": title}, unique_keys=("title",))
    )
    s.add_node(
        NodeSchema(NodeLabel.Major, properties={**dict_common, "name": name}, unique_keys=("name",))
    )
    s.add_node(
        NodeSchema(NodeLabel.University, properties={**dict_common, "name": name}, unique_keys=("name",))
    )

    # Relationships
    def rel_common() -> Dict[str, PropertySpec]:
        return {
            "eid": PropertySpec("eid", (str,), required=False),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.HAS_SKILL,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.Skill,
            properties={
                **rel_common(),
                # Accept either numeric or string mastery, and also allow numeric level_num
                "level": PropertySpec("level", (int, str), required=False),
                "level_num": PropertySpec("level_num", (int,), required=False),
                "years": PropertySpec("years", (int, float), required=False),
                "weight": PropertySpec("weight", (int, float), required=False),
            },
        )
    )
    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.WORKED_ON,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.Project,
            properties={
                **rel_common(),
                # optional time bounds
                "since": PropertySpec("since", (int, str), False),
                "until": PropertySpec("until", (int, str), False),
                # rich project metadata
                "role": PropertySpec("role", (str,), False),
                "description": PropertySpec("description", (str,), False),
                "objective": PropertySpec("objective", (str,), False),
                "contribution": PropertySpec("contribution", (str,), False),
                "impact": PropertySpec("impact", (str,), False),
                "duration": PropertySpec("duration", (str,), False),
                "collaboration_type": PropertySpec("collaboration_type", (str,), False),
                "scale": PropertySpec("scale", (str,), False),
                # lists
                "tech_stack": PropertySpec("tech_stack", (list,), False),
                "skills_applied": PropertySpec("skills_applied", (list,), False),
            },
        )
    )
    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.SPEAKS,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.Language,
            properties={
                **rel_common(),
                "level": PropertySpec("level", (int, str), False),
                "level_num": PropertySpec("level_num", (int,), False),
            },
        )
    )
    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.HAS_TITLE,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.JobTitle,
            properties={**rel_common(), "since": PropertySpec("since", (int, str), False), "until": PropertySpec("until", (int, str), False)},
        )
    )
    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.MAJORED_IN,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.Major,
            properties={**rel_common(), "degree": PropertySpec("degree", (str,), False), "gpa": PropertySpec("gpa", (int, float), False)},
        )
    )
    s.add_relationship(
        RelationshipSchema(
            rel_type=RelType.GRADUATED_FROM,
            start_label=NodeLabel.Candidate,
            end_label=NodeLabel.University,
            properties={**rel_common(), "year": PropertySpec("year", (int,), False)},
        )
    )

    return s


# A module-level default registry for convenience
SCHEMA = default_schema()
