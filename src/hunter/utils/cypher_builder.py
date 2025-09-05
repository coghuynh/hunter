from __future__ import annotations
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Optional

from hunter.domains.schema import SCHEMA, GraphSchemaError
from hunter.domains.types import NodeLabel, RelType


def _ensure_label(label: NodeLabel | str) -> NodeLabel:
    if isinstance(label, NodeLabel):
        return label
    try:
        return NodeLabel(label)
    except Exception as e:
        raise GraphSchemaError(f"Unknown label: {label}") from e


def _ensure_rel(rel: RelType | str) -> RelType:
    if isinstance(rel, RelType):
        return rel
    try:
        return RelType(rel)
    except Exception as e:
        raise GraphSchemaError(f"Unknown relationship type: {rel}") from e


def validate_node(label: NodeLabel | str, props: Mapping[str, Any]) -> None:
    lbl = _ensure_label(label)
    SCHEMA.validate_node_props(lbl, props)


def validate_relationship(
    rel_type: RelType | str,
    start_label: NodeLabel | str,
    end_label: NodeLabel | str,
    props: Mapping[str, Any],
) -> None:
    rt = _ensure_rel(rel_type)
    sl = _ensure_label(start_label)
    el = _ensure_label(end_label)
    SCHEMA.validate_relationship(rt, sl, el, props)


def build_merge_node(
    label: NodeLabel | str,
    props: Mapping[str, Any],
    merge_on: Iterable[str],
    return_alias: str = "n",
    return_field: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Safe MERGE for a node with parameterized props.
    - Validates label and property names/types against the schema.
    - `merge_on`: which props to use in the MERGE pattern.
    Returns (cypher, params).
    """
    lbl = _ensure_label(label)
    SCHEMA.validate_node_props(lbl, props)

    merge_on = list(merge_on)
    if not merge_on:
        raise GraphSchemaError("merge_on must not be empty")
    for k in merge_on:
        if k not in props:
            raise GraphSchemaError(f"merge_on key '{k}' missing in props")

    alias = return_alias
    merge_pairs = ", ".join(f"{k}: ${k}" for k in merge_on)
    set_pairs = ",\n              ".join(f"{alias}.{k} = ${k}" for k in props.keys() if k not in merge_on)
    node_schema = SCHEMA.node(lbl)
    on_create_ts = f"{alias}.created_at = datetime()" if "created_at" in node_schema.properties else None
    on_update_ts = f"{alias}.updated_at = datetime()" if "updated_at" in node_schema.properties else None
    # If node has uid property, ensure it is set on create. Include $uid param (possibly None) in params.
    on_create_uid = f"{alias}.uid = coalesce($uid, randomUUID())" if "uid" in node_schema.properties else None

    on_create_set = ",\n                          ".join(filter(None, [set_pairs, on_create_uid, on_create_ts]))
    on_match_set = ",\n                          ".join(filter(None, [set_pairs, on_update_ts]))

    ret_clause = f"RETURN {alias}.{return_field} AS {return_field}" if return_field else f"RETURN {alias}"
    q = (
        f"MERGE ({alias}:{lbl.value} {{{merge_pairs}}})\n"
        f"ON CREATE SET {on_create_set if on_create_set else ' '}\n"
        f"ON MATCH  SET {on_match_set if on_match_set else ' '}\n"
        f"{ret_clause}"
    )
    out_params = dict(props)
    if "uid" in node_schema.properties and "uid" not in out_params:
        out_params["uid"] = None
    return q, out_params


def build_link(
    start_label: NodeLabel | str,
    rel_type: RelType | str,
    end_label: NodeLabel | str,
    start_uid: str,
    end_uid: str,
    rel_props: Mapping[str, Any] | None = None,
    alias: str = "r",
    return_field: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Safe MERGE for (start)-[rel]->(end) by UIDs with optional relationship properties.
    Returns (cypher, params).
    """
    sl = _ensure_label(start_label)
    el = _ensure_label(end_label)
    rt = _ensure_rel(rel_type)
    rel_props = dict(rel_props or {})

    validate_relationship(rt, sl, el, rel_props)

    # Only allow whitelisted alias/type/labels (enforced by enums)
    set_rel = ",\n                ".join(f"{alias}.{k} = $rel_{k}" for k in rel_props.keys())
    params = {"start_uid": start_uid, "end_uid": end_uid}
    params.update({f"rel_{k}": v for k, v in rel_props.items()})
    # Always provide rel_eid param used in ON CREATE SET coalesce($rel_eid, ...)
    if "rel_eid" not in params:
        params["rel_eid"] = rel_props.get("eid") if rel_props else None

    ret_clause = f"RETURN {alias}.{return_field} AS {return_field}" if return_field else f"RETURN {alias}"
    q = (
        f"MATCH (a:{sl.value} {{uid: $start_uid}})\n"
        f"MATCH (b:{el.value} {{uid: $end_uid}})\n"
        f"MERGE (a)-[{alias}:{rt.value}]->(b)\n"
        f"ON CREATE SET {alias}.eid = coalesce($rel_eid, randomUUID()), {alias}.created_at = datetime()\n"
        f"SET {alias}.updated_at = datetime()"
        + (f",\n    {set_rel}" if set_rel else "")
        + f"\n{ret_clause}"
    )
    return q, params
