from typing import Optional, Dict, Any, List
from hunter.db import run as _run
from hunter.utils import _strip_or_none

# Helpers


# ===== Generic repositories for dictionary-like nodes =====
# Skill(name), Project(name), Language(name), JobTitle(title)

class _DictRepo:
    label: str = ""
    key_field: str = "name"  # default is `name`, override for JobTitle

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


class SkillManagement(_DictRepo):
    label = "Skill"
    key_field = "name"


class ProjectManagement(_DictRepo):
    label = "Project"
    key_field = "name"


class LanguageManagement(_DictRepo):
    label = "Language"
    key_field = "name"


class JobTitleManagement(_DictRepo):
    label = "JobTitle"
    key_field = "title"
    
class MajorManagement(_DictRepo):
    label = "Major"
    key_field = "name"
    
class UniversityManagement(_DictRepo):
    label = "University"
    key_field = "name"

