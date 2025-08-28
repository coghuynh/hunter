from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from copy import deepcopy

from hunter.db import run as _run 
from hunter.repository.feature_repo import (
  SkillManagement,
  LanguageManagement,
  ProjectManagement,
  JobTitleManagement,
  MajorManagement,
  UniversityManagement
)

# --------- Level maps ----------
SKILL_LEVEL_MAP = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}
LANG_LEVEL_MAP = {
    "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6, "native": 7
}

# --------- Defaults ----------
DEFAULT_WEIGHTS = {
    "skills": 0.6,
    "job_titles": 0.1,
    "languages": 0.05,
    "education": 0.0,   # wire later
    "keywords": 0.0,    # wire later
    "location": 0.05,
}

DEFAULT_INCLUDE_FIELDS = [
    "id", "name", "headline", "location",
    "salary_expectation", "experience_years", "skills", "job_titles", "languages"
]

# --------- Public API ----------
def match_candidates(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rank and return top-k candidates by provided features.

    payload schema (subset):
      {
        "top_k": 10,
        "must_have": {
          "skills": [{"name":"python","min_level":"advanced","min_years":2}, ...],
          "languages": [{"name":"english","min_level":"B2"}],
          "job_titles_any": ["data engineer","ml engineer"],
          "location_any": ["ho chi minh city", "remote"],
          "remote_ok": true,
          "salary_max": 2000
        },
        "nice_to_have": {
          "skills": [{"name":"pandas","weight":1.0,"prefer_min_years":0,"prefer_level":"advanced"}],
          "job_titles": ["ml engineer", "data scientist"],
          "languages": ["english", "japanese"],
          "location_preference": "ho chi minh city"
        },
        "weights": {...},
        "explain": true,
        "include_fields": ["id","name","headline","skills","location"]
      }
    """
    top_k = int(payload.get("top_k", 10))
    include_fields = payload.get("include_fields") or DEFAULT_INCLUDE_FIELDS
    explain = bool(payload.get("explain", True))
    weights = _merge_weights(payload.get("weights"))

    must_have = payload.get("must_have") or {}
    nice_to_have = payload.get("nice_to_have") or {}

    # ---- normalize must-have ----
    mh_skills = []
    for s in must_have.get("skills", []) or []:
        mh_skills.append({
            "name": _lc(s.get("name")),
            "min_level_num": _map_level(SKILL_LEVEL_MAP, s.get("min_level")),
            "min_years": _num(s.get("min_years"), 0),
        })

    mh_langs = []
    for l in must_have.get("languages", []) or []:
        mh_langs.append({
            "name": _lc(l.get("name")),
            "min_level_num": _map_level(LANG_LEVEL_MAP, l.get("min_level")),
        })

    mh_titles_any = [_lc(t) for t in (must_have.get("job_titles_any") or [])]
    mh_locations_any = [_lc(t) for t in (must_have.get("location_any") or [])]
    mh_remote_ok = must_have.get("remote_ok")
    mh_salary_max = must_have.get("salary_max")

    # ---- normalize nice-to-have ----
    nh_skill_items = []
    for s in nice_to_have.get("skills", []) or []:
        nh_skill_items.append({
            "name": _lc(s.get("name")),
            "weight": float(s.get("weight", 1.0)),
            "prefer_min_years": _num(s.get("prefer_min_years"), 0),
            "prefer_level_num": _map_level(SKILL_LEVEL_MAP, s.get("prefer_level")),
        })

    nh_titles = [_lc(t) for t in (nice_to_have.get("job_titles") or [])]
    nh_langs = [_lc(l) for l in (nice_to_have.get("languages") or [])]
    nh_location_pref = _lc(nice_to_have.get("location_preference"))

    # Build params for Cypher
    params = {
        "mustSkills": mh_skills,
        "mustLangs": mh_langs,
        "mustTitles": mh_titles_any,
        "mustLocations": mh_locations_any,
        "remoteOk": mh_remote_ok,
        "salaryMax": mh_salary_max,

        "niceSkills": nh_skill_items,
        "niceTitles": nh_titles,
        "niceLangs": nh_langs,
        "locPref": nh_location_pref,

        "W": weights,
        "topK": top_k,
    }

    rows = _run(_CYPHER_MATCH_AND_SCORE, params)

    # rows: [c_props, score, s_skills, s_titles, s_lang, s_loc]
    items = []
    for r in rows:
        c = r[0]
        score = float(r[1] or 0.0)
        s_sk, s_ti, s_la, s_lo = (float(r[2] or 0.0), float(r[3] or 0.0), float(r[4] or 0.0), float(r[5] or 0.0))

        candidate = _project_candidate(c, include_fields)
        entry = {
            "candidate": candidate,
            "score": round(score, 6),
        }
        if explain:
            reasons = []
            if s_sk > 0:
                reasons.append({
                    "kind": "skill",
                    "detail": "Matched nice-to-have skills with level/years bonuses",
                    "weight": weights["skills"],
                    "contribution": round(weights["skills"] * s_sk, 6),
                })
            if s_ti > 0:
                reasons.append({
                    "kind": "job_title",
                    "detail": "At least one preferred job title matched",
                    "weight": weights["job_titles"],
                    "contribution": round(weights["job_titles"] * s_ti, 6),
                })
            if s_la > 0:
                reasons.append({
                    "kind": "language",
                    "detail": "Proportion of requested languages satisfied",
                    "weight": weights["languages"],
                    "contribution": round(weights["languages"] * s_la, 6),
                })
            if s_lo > 0:
                reasons.append({
                    "kind": "location",
                    "detail": "Preferred city matched",
                    "weight": weights["location"],
                    "contribution": round(weights["location"] * s_lo, 6),
                })
            entry["reasons"] = reasons

        items.append(entry)

    return {"top_k": top_k, "items": items, "next_cursor": None}


# --------- Helpers ----------
def _lc(x: Optional[str]) -> Optional[str]:
    return x.lower().strip() if isinstance(x, str) and x.strip() else None

def _num(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default

def _map_level(mapper: Dict[str, int], val: Optional[str]) -> Optional[int]:
    if not val:
        return None
    v = mapper.get(str(val).lower())
    return int(v) if v is not None else None

def _merge_weights(w: Optional[Dict[str, float]]) -> Dict[str, float]:
    base = deepcopy(DEFAULT_WEIGHTS)
    if not w:
        return base
    for k, v in w.items():
        if k in base and v is not None:
            base[k] = float(v)
    return base

def _project_candidate(cprops: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    # cprops are already plain dicts (returned via c{.*} projection in Cypher)
    if not fields:
        return cprops
    out = {}
    for f in fields:
        if f in cprops:
            out[f] = cprops[f]
    # best-effort enrich: if include_fields requests derived lists but node keeps relations,
    # keep nulls; a higher layer could hydrate if needed.
    for possible in ("skills", "job_titles", "languages"):
        if possible in fields and possible not in out:
            out[possible] = None
    return out


# --------- Cypher (Community-friendly: no rel constraints) ----------
# Notes:
# - Candidate properties used (suggested): id, name, headline, location, remote_ok, salary_max (or salary_expectation.max)
# - Relations:
#    (c)-[HAS_SKILL {level_num:int, years:int}]->(sk:Skill {name})
#    (c)-[:WORKED_AS]->(t:JobTitle {title})
#    (c)-[SPEAKS {level_num:int}]->(lg:Language {name})
# Feel free to rename edge names to your schema. The query is robust to missing edges.
_CYPHER_MATCH_AND_SCORE = r"""
// ---------- base candidate scan ----------
MATCH (c:Candidate)

// must-have: remote_ok
WHERE ($remoteOk IS NULL OR c.remote_ok = $remoteOk)

// must-have: salary budget (use c.salary_max if you store it; otherwise adapt to your structure)
AND ($salaryMax IS NULL OR coalesce(c.salary_max, c.salary_expectation.max) <= $salaryMax)

// must-have: job title any-of
AND (
  size($mustTitles) = 0 OR EXISTS {
    MATCH (c)-[:HAS_TITLE]->(jt:JobTitle)
    WHERE toLower(jt.title) IN $mustTitles
  }
)

// must-have: location any-of (exact, case-insensitive)
AND (
  size($mustLocations) = 0 OR toLower(coalesce(c.location, "")) IN $mustLocations
)

// must-have: languages (all)
AND (
  size($mustLangs) = 0 OR ALL(req IN $mustLangs WHERE EXISTS {
    MATCH (c)-[sp:SPEAKS]->(lg:Language)
    WHERE toLower(lg.name) = req.name
      AND coalesce(sp.level_num, 0) >= coalesce(req.min_level_num, 0)
  })
)

// must-have: skills (all)
AND (
  size($mustSkills) = 0 OR ALL(ms IN $mustSkills WHERE EXISTS {
    MATCH (c)-[hs:HAS_SKILL]->(sk:Skill)
    WHERE toLower(sk.name) = ms.name
      AND coalesce(hs.level_num, 0) >= coalesce(ms.min_level_num, 0)
      AND coalesce(hs.years, 0) >= coalesce(ms.min_years, 0)
  })
)

// -------- collect facets once to avoid repeated scans --------
OPTIONAL MATCH (c)-[hs:HAS_SKILL]->(sk:Skill)
WITH c,
     collect({name: toLower(sk.name), level_num: hs.level_num, years: hs.years}) AS CSkills

OPTIONAL MATCH (c)-[:HAS_TITLE]->(jt:JobTitle)
WITH c, CSkills, collect(toLower(jt.title)) AS CTitles

OPTIONAL MATCH (c)-[sp:SPEAKS]->(lg:Language)
WITH c, CSkills, CTitles, collect({name: toLower(lg.name), level_num: sp.level_num}) AS CLangs

// -------- scores --------

// Skills score: average over niceSkills (presence × (0.7*level + 0.3*years bonus))
// level_num normalized by /4.0 ; years soft-capped at prefer_min_years+5 then /5.0
WITH c, CSkills, CTitles, CLangs,
  CASE WHEN size($niceSkills)=0 THEN 0.0 ELSE
    reduce(acc=0.0, ns IN $niceSkills |
      acc + CASE
        WHEN ANY(cs IN CSkills WHERE cs.name = ns.name) THEN
          ns.weight * (
            0.7 * (1.0 * head([cs IN CSkills WHERE cs.name = ns.name]).level_num / 4.0) +
            0.3 * (
              1.0 * (
                CASE
                  WHEN coalesce(head([cs IN CSkills WHERE cs.name = ns.name]).years, 0) <= coalesce(ns.prefer_min_years, 0) + 5
                    THEN coalesce(head([cs IN CSkills WHERE cs.name = ns.name]).years, 0)
                  ELSE coalesce(ns.prefer_min_years, 0) + 5
                END
              ) / 5.0
            )
          )
        ELSE 0.0 END
    ) / (1.0 * size($niceSkills)) END AS S_skills

// Titles score: binary any-match among preferred
WITH c, CSkills, CTitles, CLangs, S_skills,
  CASE
    WHEN size($niceTitles)=0 THEN 0.0
    WHEN any(t IN CTitles WHERE t IN $niceTitles) THEN 1.0 ELSE 0.0
  END AS S_titles

// Languages score: proportion of requested nice-to-have languages present (level disregarded, keep simple)
// If you want level-aware, mirror the must-have approach and add prefer level.
WITH c, CSkills, CTitles, CLangs, S_skills, S_titles,
  CASE
    WHEN size($niceLangs)=0 THEN 0.0
    ELSE
      reduce(hit=0.0, ln IN $niceLangs |
        hit + CASE WHEN any(cl IN CLangs WHERE cl.name = ln) THEN 1.0 ELSE 0.0 END
      ) / (1.0 * size($niceLangs))
  END AS S_langs

// Location score: 1.0 if preferred city matched (exact, case-insensitive)
WITH c, S_skills, S_titles, S_langs,
  CASE WHEN $locPref IS NULL OR $locPref = "" THEN 0.0
       WHEN toLower(coalesce(c.location, "")) = $locPref THEN 1.0
       ELSE 0.0 END AS S_loc

// Final score
WITH c, S_skills, S_titles, S_langs, S_loc,
  coalesce($W.skills, 0.0)*S_skills +
  coalesce($W.job_titles, 0.0)*S_titles +
  coalesce($W.languages, 0.0)*S_langs +
  coalesce($W.location, 0.0)*S_loc
  AS final_score

RETURN
  c{ .* } AS cprops,
  final_score AS score,
  S_skills, S_titles, S_langs, S_loc
ORDER BY score DESC, coalesce(c.experience_years,0) DESC, coalesce(c.salary_max, 9e18) ASC
LIMIT $topK
"""