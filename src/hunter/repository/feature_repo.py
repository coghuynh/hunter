from typing import Optional, Dict, Any, List
from hunter.db import run as _run
from hunter.utils import _strip_or_none
from hunter.domains.schema import SCHEMA
from hunter.domains.types import NodeLabel, RelType
from hunter.utils.cypher_builder import build_merge_node, build_link

# ===== Generic repositories for dictionary-like nodes =====
# Skill(name), Project(name), Language(name), JobTitle(title)

class _DictRepo:
    label: NodeLabel  # concrete subclasses must set
    key_field: str = "name"  # default is `name`, override for JobTitle

    # Relationship type from Candidate -> this label. Override in subclasses.
    rel_type: RelType

    @classmethod
    def upsert(cls, name: str, uid: Optional[str] = None) -> str:
        name = _strip_or_none(name)
        if not name:
            raise ValueError("name must be non-empty")

        props: Dict[str, Any]
        merge_on: List[str]
        if uid:
            props = {"uid": uid, cls.key_field: name}
            merge_on = ["uid"]
        else:
            # Merge by the dictionary unique key (e.g., name/title)
            props = {cls.key_field: name}
            merge_on = [cls.key_field]

        # Validate props using schema and use safe builder
        SCHEMA.validate_node_props(cls.label, props)
        q, params = build_merge_node(cls.label, props, merge_on=merge_on, return_alias="n", return_field="uid")
        rows = _run(q, params)
        return rows[0][0]

    @classmethod
    def get_by_uids(cls, uids: List[str]) -> List[Dict[str, Any]]:
        if not uids:
            return []
        q = (
            f"""
            MATCH (n:{cls.label.value})
            WHERE n.uid IN $uids
            RETURN n.uid AS uid, n.{cls.key_field} AS name
            ORDER BY n.{cls.key_field}
            """
        )
        rows = _run(q, {"uids": list(uids)})
        return [{"uid": u, cls.key_field: n} for (u, n) in rows]

    @classmethod
    def get_by_name(cls, name: str) -> Optional[Dict[str, Any]]:
        name = _strip_or_none(name)
        if not name:
            return None
        q = (
            f"""
            MATCH (n:{cls.label.value} {{{cls.key_field}: $name}})
            RETURN n.uid AS uid, n.{cls.key_field} AS name
            LIMIT 1
            """
        )
        rows = _run(q, {"name": name})
        if not rows:
            return None
        return {"uid": rows[0][0], cls.key_field: rows[0][1]}

    @classmethod
    def get_list(cls, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        q = (
            f"""
            MATCH (n:{cls.label.value})
            RETURN n.uid AS uid, n.{cls.key_field} AS name
            ORDER BY n.{cls.key_field}
            SKIP $skip LIMIT $limit
            """
        )
        rows = _run(q, {"skip": int(skip), "limit": int(limit)})
        return [{"uid": u, cls.key_field: n} for (u, n) in rows]

    @classmethod
    def delete(cls, uid: str) -> int:
        q = (
            f"""
            MATCH (n:{cls.label.value} {{uid:$uid}})
            DETACH DELETE n
            RETURN 1 AS deleted
            """
        )
        rows = _run(q, {"uid": uid})
        return 1 if rows else 0

    @classmethod
    def link_by_uids(
        cls,
        candidate_uid: str,
        feature_uid: str,
        rel_props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create/merge (Candidate)-[REL]->(Feature) by UIDs. Returns relationship eid.
        rel_props can hold optional relationship properties (e.g., weight, level, since, etc.).
        """
        if not cls.rel_type:
            raise ValueError("rel_type must be defined on the concrete repo class")
        if not candidate_uid or not feature_uid:
            raise ValueError("candidate_uid and feature_uid must be non-empty")

        rel_props = rel_props or {}
        # Validate relationship shape before executing
        SCHEMA.validate_relationship(
            cls.rel_type,
            NodeLabel.Candidate,
            cls.label,
            rel_props,
        )
        # Build safe link query
        q, params = build_link(
            start_label=NodeLabel.Candidate,
            rel_type=cls.rel_type,
            end_label=cls.label,
            start_uid=candidate_uid,
            end_uid=feature_uid,
            rel_props=rel_props,
            alias="r",
            return_field="eid",
        )
        # ensure possible rel_eid param is present if user provided
        if "rel_eid" not in params:
            params["rel_eid"] = rel_props.get("eid") if rel_props else None
        rows = _run(q, params)
        return rows[0][0]

    @classmethod
    def link_by_name(
        cls,
        candidate_uid: str,
        name: str,
        rel_props: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Upsert the feature by name/title and link to Candidate. Returns relationship eid."""
        feature_uid = cls.upsert(name)
        return cls.link_by_uids(candidate_uid, feature_uid, rel_props)

    @classmethod
    def unlink_by_uids(cls, candidate_uid: str, feature_uid: str) -> int:
        """Delete a specific relationship between Candidate and a feature by UIDs. Returns 1 if deleted, else 0."""
        if not cls.rel_type:
            raise ValueError("rel_type must be defined on the concrete repo class")
        q = (
            f"""
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type.value}]->(n:{cls.label.value} {{uid: $feature_uid}})
            DELETE r
            RETURN 1 AS deleted
            """
        )
        rows = _run(q, {"candidate_uid": candidate_uid, "feature_uid": feature_uid})
        return 1 if rows else 0

    @classmethod
    def list_for_candidate(cls, candidate_uid: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List features of this type attached to a Candidate, returning minimal fields."""
        if not cls.rel_type:
            raise ValueError("rel_type must be defined on the concrete repo class")
        q = (
            f"""
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type.value}]->(n:{cls.label.value})
            RETURN n.uid AS uid, n.{cls.key_field} AS name, r.eid AS rel_eid, properties(r) AS rel_props
            ORDER BY n.{cls.key_field}
            SKIP $skip LIMIT $limit
            """
        )
        rows = _run(q, {"candidate_uid": candidate_uid, "skip": int(skip), "limit": int(limit)})
        out: List[Dict[str, Any]] = []
        for uid, name, rel_eid, rel_dict in rows:
            item = {"uid": uid, cls.key_field: name, "rel_eid": rel_eid}
            if isinstance(rel_dict, dict):
                # include relationship properties (e.g., weight, level, since)
                item.update({f"rel_{k}": v for k, v in rel_dict.items()})
            out.append(item)
        return out

    @classmethod
    def unlink_all_for_candidate(cls, candidate_uid: str) -> int:
        """Remove all relationships of this type from a Candidate. Returns count deleted."""
        if not cls.rel_type:
            raise ValueError("rel_type must be defined on the concrete repo class")
        q = (
            f"""
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type.value}]->(:{cls.label.value})
            WITH r
            DELETE r
            RETURN count(*) AS cnt
            """
        )
        rows = _run(q, {"candidate_uid": candidate_uid})
        return rows[0][0] if rows else 0


class SkillManagement(_DictRepo):
    label = NodeLabel.Skill
    key_field = "name"
    rel_type = RelType.HAS_SKILL


class ProjectManagement(_DictRepo):
    label = NodeLabel.Project
    key_field = "name"
    rel_type = RelType.WORKED_ON


class LanguageManagement(_DictRepo):
    label = NodeLabel.Language
    key_field = "name"
    rel_type = RelType.SPEAKS


class JobTitleManagement(_DictRepo):
    label = NodeLabel.JobTitle
    key_field = "title"
    rel_type = RelType.HAS_TITLE
    
class MajorManagement(_DictRepo):
    label = NodeLabel.Major
    key_field = "name"
    rel_type = RelType.MAJORED_IN
    
class UniversityManagement(_DictRepo):
    label = NodeLabel.University
    key_field = "name"
    rel_type = RelType.GRADUATED_FROM
