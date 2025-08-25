"""
Repository layer for Candidate-centric data access.

This module encapsulates Cypher/ORM interactions to:
- Upsert candidates
- Attach features (skills, languages, education, job titles, projects)
- Fetch candidate details and neighbors
- List / delete candidates

Design goals:
- Parameterized Cypher (plan cache, safety)
- Bulk-friendly operations via UNWIND
- Keep business logic out of repository (no TF-IDF etc.)
"""
from __future__ import annotations

from typing import Iterable, List, Dict, Any, Optional
from hunter.db import db_instance as db

# -----------------------------
# Candidate CRUD
# -----------------------------

def upsert_candidate(name: str, location: Optional[str] = None, uid: Optional[str] = None) -> str:
    """Create or update a Candidate.

    If `uid` is provided, merge by uid; else merge by (name) and create uid via randomUUID().
    Returns the candidate uid.
    """
    if uid:
        q = (
            """
            MERGE (c:Candidate {uid: $uid})
            ON CREATE SET c.name = $name, c.location = $location, c.created_at = datetime()
            ON MATCH  SET c.name = $name, c.location = coalesce($location, c.location), c.updated_at = datetime()
            RETURN c.uid AS uid
            """
        )
        rows, _ = db.cypher_query(q, {"uid": uid, "name": name.strip(), "location": location})
        return rows[0][0]
    else:
        q = (
            """
            MERGE (c:Candidate {name: $name})
            ON CREATE SET c.uid = randomUUID(), c.location = $location, c.created_at = datetime()
            ON MATCH  SET c.location = coalesce($location, c.location), c.updated_at = datetime()
            RETURN c.uid AS uid
            """
        )
        rows, _ = db.cypher_query(q, {"name": name.strip(), "location": location})
        return rows[0][0]


def get_candidate_by_uid(uid: str) -> Optional[Dict[str, Any]]:
    q = """
    MATCH (c:Candidate {uid:$uid})
    RETURN c.uid AS uid, c.name AS name, c.location AS location
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    if not rows:
        return None
    r = rows[0]
    return {"uid": r[0], "name": r[1], "location": r[2]}


def list_candidates(skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    q = """
    MATCH (c:Candidate)
    RETURN c.uid AS uid, c.name AS name, c.location AS location
    ORDER BY c.name
    SKIP $skip LIMIT $limit
    """
    rows, _ = db.cypher_query(q, {"skip": int(skip), "limit": int(limit)})
    return [{"uid": a, "name": b, "location": c} for (a, b, c) in rows]


def delete_candidate(uid: str) -> int:
    """Detach-delete one candidate. Returns number of nodes deleted (0/1)."""
    q = """
    MATCH (c:Candidate {uid:$uid})
    DETACH DELETE c
    RETURN 1 AS deleted
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    return 1 if rows else 0


# -----------------------------
# Attach features (bulk-friendly)
# -----------------------------

def attach_job_titles(candidate_uid: str, titles: Iterable[str]) -> None:
    """Attach WORK_AS (unweighted) from JobTitle -> Candidate.
    Titles will be MERGE'd by exact text; ensure uniqueness via constraint on JobTitle.title.
    """
    titles = [t for t in (titles or []) if t and str(t).strip()]
    if not titles:
        return
    q = """
    UNWIND $rows AS row
    MATCH (c:Candidate {uid:$cid})
    MERGE (jt:JobTitle {title: row.title})
      ON CREATE SET jt.uid = randomUUID()
    MERGE (jt)-[r:WORK_AS]->(c)
    SET r.weight = 1.0, r.cost = 1.0,
        r.updated_at = datetime(), r.eid = coalesce(r.eid, randomUUID())
    """
    rows = [{"title": str(t).strip()} for t in titles]
    db.cypher_query(q, {"cid": candidate_uid, "rows": rows})


def attach_skills(candidate_uid: str, skills: Iterable[Dict[str, Any]]) -> None:
    """Attach HAS_SKILL edges with weights.

    `skills`: iterable of dicts with keys:
      - name (str, required)
      - weight (float, optional) in [0,1]
      - last_used (str/datetime, optional)
      - core (bool, optional)
      - endorse (int, optional)
    """
    rows = []
    for s in skills or []:
        name = str(s.get("name", "")).strip().lower()
        if not name:
            continue
        w = s.get("weight")
        w = float(w) if w is not None else None
        rows.append({
            "name": name,
            "w": w,
            "last_used": s.get("last_used"),
            "core": bool(s.get("core")) if s.get("core") is not None else None,
            "endorse": int(s.get("endorse", 0)) if s.get("endorse") is not None else None,
        })
    if not rows:
        return
    q = """
    UNWIND $rows AS row
    MATCH (c:Candidate {uid:$cid})
    MERGE (s:Skill {name: row.name})
      ON CREATE SET s.uid = randomUUID()
    MERGE (s)-[r:HAS_SKILL]->(c)
    SET r.last_used = coalesce(row.last_used, r.last_used),
        r.core = coalesce(row.core, r.core),
        r.endorse = coalesce(row.endorse, r.endorse),
        r.updated_at = datetime(),
        r.eid = coalesce(r.eid, randomUUID())
    WITH r, row
    CALL {
      WITH r, row
      WITH r, row.w AS w
      CALL {
        WITH r, w
        WITH r, CASE WHEN w IS NULL THEN r.weight ELSE toFloat(w) END AS newW
        SET r.weight = coalesce(newW, 1.0),
            r.cost = CASE WHEN coalesce(newW,1.0) > 0 THEN 1.0 / coalesce(newW,1.0) ELSE 1.0 END
        RETURN 0 AS _
      }
      RETURN 0 AS _
    }
    """
    db.cypher_query(q, {"cid": candidate_uid, "rows": rows})


def attach_languages(candidate_uid: str, languages: Iterable[Dict[str, Any]]) -> None:
    """Attach SPEAK edges with optional CEFR level/weight.

    Each item may include:
      - name (str, required)
      - weight (float, optional) in [0,1]
      - level (str, optional), e.g., A1..C2
      - last_used (str/datetime, optional)
    """
    rows = []
    for l in languages or []:
        name = str(l.get("name", "")).strip().lower()
        if not name:
            continue
        rows.append({
            "name": name,
            "w": float(l.get("weight")) if l.get("weight") is not None else None,
            "level": l.get("level"),
            "last_used": l.get("last_used"),
        })
    if not rows:
        return
    q = """
    UNWIND $rows AS row
    MATCH (c:Candidate {uid:$cid})
    MERGE (l:Language {name: row.name})
      ON CREATE SET l.uid = randomUUID()
    MERGE (l)-[r:SPEAK]->(c)
    SET r.level = coalesce(row.level, r.level),
        r.last_used = coalesce(row.last_used, r.last_used),
        r.updated_at = datetime(),
        r.eid = coalesce(r.eid, randomUUID())
    WITH r, row
    CALL {
      WITH r, row
      WITH r, row.w AS w
      CALL {
        WITH r, w
        WITH r, CASE WHEN w IS NULL THEN r.weight ELSE toFloat(w) END AS newW
        SET r.weight = coalesce(newW, 1.0),
            r.cost = CASE WHEN coalesce(newW,1.0) > 0 THEN 1.0 / coalesce(newW,1.0) ELSE 1.0 END
        RETURN 0 AS _
      }
      RETURN 0 AS _
    }
    """
    db.cypher_query(q, {"cid": candidate_uid, "rows": rows})


def attach_education(candidate_uid: str, items: Iterable[Dict[str, Any]]) -> None:
    """Attach STUDIED edges.

    Each item may include:
      - school (str, required)
      - degree (str, optional)
      - gpa (float, optional)
      - from_date / to_date (str/datetime, optional)
      - weight (float, optional)
    """
    rows = []
    for e in items or []:
        school = str(e.get("school", "")).strip()
        if not school:
            continue
        rows.append({
            "school": school,
            "degree": e.get("degree"),
            "gpa": e.get("gpa"),
            "from_date": e.get("from_date"),
            "to_date": e.get("to_date"),
            "w": float(e.get("weight")) if e.get("weight") is not None else None,
        })
    if not rows:
        return
    q = """
    UNWIND $rows AS row
    MATCH (c:Candidate {uid:$cid})
    MERGE (e:Education {school: row.school})
      ON CREATE SET e.uid = randomUUID()
    MERGE (e)-[r:STUDIED]->(c)
    SET r.degree = coalesce(row.degree, r.degree),
        r.gpa = coalesce(row.gpa, r.gpa),
        r.fromDate = CASE WHEN row.from_date IS NULL THEN r.fromDate ELSE datetime(row.from_date) END,
        r.toDate   = CASE WHEN row.to_date   IS NULL THEN r.toDate   ELSE datetime(row.to_date)   END,
        r.updated_at = datetime(),
        r.eid = coalesce(r.eid, randomUUID())
    WITH r, row
    CALL {
      WITH r, row
      WITH r, row.w AS w
      CALL {
        WITH r, w
        WITH r, CASE WHEN w IS NULL THEN r.weight ELSE toFloat(w) END AS newW
        SET r.weight = coalesce(newW, 1.0),
            r.cost = CASE WHEN coalesce(newW,1.0) > 0 THEN 1.0 / coalesce(newW,1.0) ELSE 1.0 END
        RETURN 0 AS _
      }
      RETURN 0 AS _
    }
    """
    db.cypher_query(q, {"cid": candidate_uid, "rows": rows})


def attach_projects(candidate_uid: str, items: Iterable[Dict[str, Any]]) -> None:
    """Attach WORK_ON edges.

    Each item may include:
      - name (str, required)
      - domain (str, optional)
      - objective (str, optional)
      - weight (float, optional)
    """
    rows = []
    for p in items or []:
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        rows.append({
            "name": name,
            "domain": p.get("domain"),
            "objective": p.get("objective"),
            "w": float(p.get("weight")) if p.get("weight") is not None else None,
        })
    if not rows:
        return
    q = """
    UNWIND $rows AS row
    MATCH (c:Candidate {uid:$cid})
    MERGE (p:Project {name: row.name})
      ON CREATE SET p.uid = randomUUID(), p.domain = row.domain, p.objective = row.objective
    MERGE (p)-[r:WORK_ON]->(c)
    SET r.updated_at = datetime(), r.eid = coalesce(r.eid, randomUUID())
    WITH r, row
    CALL {
      WITH r, row
      WITH r, row.w AS w
      CALL {
        WITH r, w
        WITH r, CASE WHEN w IS NULL THEN r.weight ELSE toFloat(w) END AS newW
        SET r.weight = coalesce(newW, 1.0),
            r.cost = CASE WHEN coalesce(newW,1.0) > 0 THEN 1.0 / coalesce(newW,1.0) ELSE 1.0 END
        RETURN 0 AS _
      }
      RETURN 0 AS _
    }
    """
    db.cypher_query(q, {"cid": candidate_uid, "rows": rows})


# -----------------------------
# Fetch neighbors (features of a candidate)
# -----------------------------

def get_candidate_neighbors(uid: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return all feature neighbors grouped by type.

    Output keys: skills, languages, education, projects, titles
    """
    out: Dict[str, List[Dict[str, Any]]] = {
        "skills": [],
        "languages": [],
        "education": [],
        "projects": [],
        "titles": [],
    }

    # Skills
    q = """
    MATCH (s:Skill)-[r:HAS_SKILL]->(c:Candidate {uid:$uid})
    RETURN s.name AS name, r.weight AS weight, r.cost AS cost, r.last_used AS last_used, r.core AS core, r.endorse AS endorse
    ORDER BY weight DESC
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    out["skills"] = [
        {"name": a, "weight": b, "cost": c, "last_used": d, "core": e, "endorse": f}
        for (a, b, c, d, e, f) in rows
    ]

    # Languages
    q = """
    MATCH (l:Language)-[r:SPEAK]->(c:Candidate {uid:$uid})
    RETURN l.name AS name, r.weight AS weight, r.cost AS cost, r.level AS level, r.last_used AS last_used
    ORDER BY weight DESC
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    out["languages"] = [
        {"name": a, "weight": b, "cost": c, "level": d, "last_used": e}
        for (a, b, c, d, e) in rows
    ]

    # Education
    q = """
    MATCH (e:Education)-[r:STUDIED]->(c:Candidate {uid:$uid})
    RETURN e.school AS school, r.degree AS degree, r.gpa AS gpa, r.weight AS weight, r.cost AS cost,
           r.fromDate AS fromDate, r.toDate AS toDate
    ORDER BY weight DESC
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    out["education"] = [
        {"school": a, "degree": b, "gpa": c, "weight": d, "cost": e, "fromDate": f, "toDate": g}
        for (a, b, c, d, e, f, g) in rows
    ]

    # Projects
    q = """
    MATCH (p:Project)-[r:WORK_ON]->(c:Candidate {uid:$uid})
    RETURN p.name AS name, p.domain AS domain, p.objective AS objective, r.weight AS weight, r.cost AS cost
    ORDER BY weight DESC
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    out["projects"] = [
        {"name": a, "domain": b, "objective": c, "weight": d, "cost": e}
        for (a, b, c, d, e) in rows
    ]

    # Titles
    q = """
    MATCH (jt:JobTitle)-[r:WORK_AS]->(c:Candidate {uid:$uid})
    RETURN jt.title AS title, r.weight AS weight, r.cost AS cost
    ORDER BY title
    """
    rows, _ = db.cypher_query(q, {"uid": uid})
    out["titles"] = [
        {"title": a, "weight": b, "cost": c}
        for (a, b, c) in rows
    ]

    return out
