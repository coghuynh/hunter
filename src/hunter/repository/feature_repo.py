from typing import Optional, Dict, Any, List
from hunter.db import run as _run
from hunter.utils import _strip_or_none

# ===== Generic repositories for dictionary-like nodes =====
# Skill(name), Project(name), Language(name), JobTitle(title)

class _DictRepo:
    label: str = ""
    key_field: str = "name"  # default is `name`, override for JobTitle

    # Relationship type from Candidate -> this label. Override in subclasses.
    rel_type: str = ""

    @classmethod
    def upsert(cls, name: str, uid: Optional[str] = None) -> str:
        name = _strip_or_none(name)
        if not name:
            raise ValueError("name must be non-empty")

        if uid:
            q = (
                f"""
                MERGE (n:{cls.label} {{uid: $uid}})
                ON CREATE SET n.{cls.key_field} = $name, n.created_at = datetime()
                ON MATCH  SET n.{cls.key_field} = $name, n.updated_at = datetime()
                RETURN n.uid AS uid
                """
            )
            rows = _run(q, {"uid": uid, "name": name})
            return rows[0][0]
        else:
            # Merge by the dictionary unique key (e.g., name/title)
            q = (
                f"""
                MERGE (n:{cls.label} {{{cls.key_field}: $name}})
                ON CREATE SET n.uid = randomUUID(), n.created_at = datetime()
                ON MATCH  SET n.updated_at = datetime()
                RETURN n.uid AS uid
                """
            )
            rows = _run(q, {"name": name})
            return rows[0][0]

    @classmethod
    def get_by_uids(cls, uids: List[str]) -> List[Dict[str, Any]]:
        if not uids:
            return []
        q = (
            f"""
            MATCH (n:{cls.label})
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
            MATCH (n:{cls.label} {{{cls.key_field}: $name}})
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
            MATCH (n:{cls.label})
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
            MATCH (n:{cls.label} {{uid:$uid}})
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
        # Safe to embed since rel_type and label are class-defined (whitelisted), not user input.
        q = (
            f"""
            MATCH (c:Candidate {{uid: $candidate_uid}})
            MATCH (n:{cls.label} {{uid: $feature_uid}})
            MERGE (c)-[r:{cls.rel_type}]->(n)
            ON CREATE SET r.eid = coalesce($eid, randomUUID()), r.created_at = datetime()
            SET r += $rel_props,
                r.updated_at = datetime()
            RETURN r.eid AS eid
            """
        )
        rows = _run(q, {
            "candidate_uid": candidate_uid,
            "feature_uid": feature_uid,
            "rel_props": rel_props,
            "eid": rel_props.get("eid") if rel_props else None,
        })
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
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type}]->(n:{cls.label} {{uid: $feature_uid}})
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
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type}]->(n:{cls.label})
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
            MATCH (c:Candidate {{uid: $candidate_uid}})-[r:{cls.rel_type}]->(:{cls.label})
            WITH r
            DELETE r
            RETURN count(*) AS cnt
            """
        )
        rows = _run(q, {"candidate_uid": candidate_uid})
        return rows[0][0] if rows else 0


class SkillManagement(_DictRepo):
    label = "Skill"
    key_field = "name"
    rel_type = "HAS_SKILL"


class ProjectManagement(_DictRepo):
    label = "Project"
    key_field = "name"
    rel_type = "WORKED_ON"


class LanguageManagement(_DictRepo):
    label = "Language"
    key_field = "name"
    rel_type = "SPEAKS"


class JobTitleManagement(_DictRepo):
    label = "JobTitle"
    key_field = "title"
    rel_type = "HAS_TITLE"
    
class MajorManagement(_DictRepo):
    label = "Major"
    key_field = "name"
    rel_type = "MAJORED_IN"
    
class UniversityManagement(_DictRepo):
    label = "University"
    key_field = "name"
    rel_type = "GRADUATED_FROM"
