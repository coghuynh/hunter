from typing import Optional, Dict, Any, List
from hunter.db import run as _run
from hunter.utils import _strip_or_none


class CandidateRepository:
    """
    CRUD-ish operations for Candidate nodes.
    Fields used here: uid (UUID), name (str), location (str | None)
    """

    @staticmethod
    def upsert(name: str, location: Optional[str] = None, uid: Optional[str] = None) -> str:
        """
        Create or update a Candidate.
        - If uid is provided: MERGE by uid, set/refresh name/location.
        - Otherwise: MERGE by (name) as a practical natural key and assign uid on create.
        Returns the candidate uid.
        """
        name = _strip_or_none(name)
        location = _strip_or_none(location)
        if not name:
            raise ValueError("name must be non-empty")

        if uid:
            q = """
            MERGE (c:Candidate {uid: $uid})
            ON CREATE SET c.name = $name,
                          c.location = $location,
                          c.created_at = datetime()
            ON MATCH  SET c.name = $name,
                          c.location = coalesce($location, c.location),
                          c.updated_at = datetime()
            RETURN c.uid AS uid
            """
            rows = _run(q, {"uid": uid, "name": name, "location": location})
            return rows[0][0]
        else:
            q = """
            MERGE (c:Candidate {name: $name})
            ON CREATE SET c.uid = randomUUID(),
                          c.location = $location,
                          c.created_at = datetime()
            ON MATCH  SET c.location = coalesce($location, c.location),
                          c.updated_at = datetime()
            RETURN c.uid AS uid
            """
            rows = _run(q, {"name": name, "location": location})
            return rows[0][0]

    @staticmethod
    def get_by_uids(uids: List[str]) -> List[Dict[str, Any]]:
        """
        Bulk-get candidates by uid list.
        Returns: [{uid, name, location}, ...] ordered by name.
        """
        if not uids:
            return []
        q = """
        MATCH (c:Candidate)
        WHERE c.uid IN $uids
        RETURN c.uid AS uid, c.name AS name, c.location AS location
        ORDER BY c.name
        """
        rows = _run(q, {"uids": list(uids)})
        return [{"uid": u, "name": n, "location": loc} for (u, n, loc) in rows]

    @staticmethod
    def get_by_name(name: str, lim: int) -> Optional[List[Dict[str, Any]]]:
        """
        Exact-lookup by name. Returns one record (first match) or None.
        """
        name = _strip_or_none(name)
        if not name:
            return None
        q = """
        MATCH (c:Candidate {name: $name})
        RETURN c.uid AS uid, c.name AS name, c.location AS location
        LIMIT $lim
        """
        rows = _run(q, {"name": name, "lim": lim})
        if not rows:
            return None
        u, n, loc = rows[0]
        return {"uid": u, "name": n, "location": loc}

    @staticmethod
    def get_list(skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List candidates ordered by name with pagination.
        """
        q = """
        MATCH (c:Candidate)
        RETURN c.uid AS uid, c.name AS name, c.location AS location
        ORDER BY c.name
        SKIP $skip LIMIT $limit
        """
        rows = _run(q, {"skip": int(skip), "limit": int(limit)})
        return [{"uid": u, "name": n, "location": loc} for (u, n, loc) in rows]

    @staticmethod
    def delete(uid: str) -> int:
        """
        Detach-delete one candidate by uid.
        Returns 1 if a node was deleted, else 0.
        """
        q = """
        MATCH (c:Candidate {uid:$uid})
        DETACH DELETE c
        RETURN 1 AS deleted
        """
        rows = _run(q, {"uid": uid})
        return 1 if rows else 0