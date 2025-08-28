from hunter.repository.candidate_repo import CandidateRepository
from hunter.repository.feature_repo import (
    SkillManagement,
    LanguageManagement,
    ProjectManagement,
    JobTitleManagement,
    MajorManagement,
    UniversityManagement
)

from typing import Dict, Any, List, Optional
from datetime import datetime
from hunter.utils import _norm_str

# -----------------------------
# Helpers
# -----------------------------

_MASTERY_TO_WEIGHT = {
    None: None,
    "beginner": 0.3,
    "intermediate": 0.6,
    "expert": 0.9,
    # common typos / variants
    "basics": 0.3,
    "basic": 0.3,
    "less than 1 year": 0.3,
    "6 months": 0.3,
    "12 months": 0.6,
}



def _weight_from_mastery(masterry: Optional[str]) -> Optional[float]:
    if masterry is None:
        return None
    key = str(masterry).strip().lower()
    return _MASTERY_TO_WEIGHT.get(key, None)


# -----------------------------
# Service
# -----------------------------

def add_candidate_from_resume(resume: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create/Upsert a Candidate node from a parsed resume JSON and link features.

    Expected keys in `resume` (best-effort, missing keys are skipped):
      - name: str (required)
      - job_title: List[str]
      - foreign_languages: List[str]
      - majors: List[str]
      - graduated_from: List[str]  # universities / schools
      - skills: List[{"skill": str, "mastery": Optional[str]}]
      - projects: List[ProjectDict] where each project may include:
          title, description, role, tech_stack (List[str]), skills_applied (List[str]),
          duration, objective, contribution, impact, collaboration_type, scale

    Returns a summary dict with created candidate uid and counts per feature type.
    """
    name = _norm_str(resume.get("name"))
    if not name:
        raise ValueError("resume['name'] must be non-empty")

    # 1) Upsert Candidate
    cand_uid = CandidateRepository.upsert(name)

    summary = {
        "candidate_uid": cand_uid,
        "linked": {"job_titles": 0, "languages": 0, "majors": 0, "universities": 0, "skills": 0, "projects": 0},
        "skipped": [],
    }

    # 2) Job Titles
    for jt in resume.get("job_title", []) or []:
        jt_name = _norm_str(jt)
        if not jt_name:
            continue
        JobTitleManagement.link_by_name(cand_uid, jt_name)
        summary["linked"]["job_titles"] += 1

    # 3) Languages
    for lang in resume.get("foreign_languages", []) or []:
        l = _norm_str(lang)
        if not l:
            continue
        LanguageManagement.link_by_name(cand_uid, l)
        summary["linked"]["languages"] += 1

    # 4) Majors
    for m in resume.get("majors", []) or []:
        mm = _norm_str(m)
        if not mm:
            continue
        MajorManagement.link_by_name(cand_uid, mm)
        summary["linked"]["majors"] += 1

    # 5) Universities / Schools
    for u in resume.get("graduated_from", []) or []:
        uu = _norm_str(u)
        if not uu:
            continue
        UniversityManagement.link_by_name(cand_uid, uu)
        summary["linked"]["universities"] += 1

    # 6) Skills with mastery → weight on relationship
    skills: List[Dict[str, Any]] = resume.get("skills", []) or []
    for s in skills:
        s_name = _norm_str(s.get("skill")) if isinstance(s, dict) else _norm_str(s)
        if not s_name:
            continue
        mastery = None
        if isinstance(s, dict):
            mastery = _norm_str(s.get("mastery"))
        rel_props = {
            "level": mastery,
            "weight": _weight_from_mastery(mastery),
        }
        # Drop None props to keep the graph clean
        rel_props = {k: v for k, v in rel_props.items() if v is not None}
        SkillManagement.link_by_name(cand_uid, s_name, rel_props=rel_props or None)
        summary["linked"]["skills"] += 1

    # 7) Projects (link candidate → project title, attach rich props on the relationship)
    projects: List[Dict[str, Any]] = resume.get("projects", []) or []
    for p in projects:
        title = _norm_str(p.get("title")) if isinstance(p, dict) else None
        if not title:
            # if there's no usable title, skip but record
            summary["skipped"].append({"project": p, "reason": "missing title"})
            continue
        rel_props = {
            "role": _norm_str(p.get("role")),
            "description": _norm_str(p.get("description")),
            "objective": _norm_str(p.get("objective")),
            "contribution": _norm_str(p.get("contribution")),
            "impact": _norm_str(p.get("impact")),
            "duration": _norm_str(p.get("duration")),
            "collaboration_type": _norm_str(p.get("collaboration_type")),
            "scale": _norm_str(p.get("scale")),
        }
        # allow lists on rel props (Neo4j supports list-typed props)
        tech_stack = p.get("tech_stack") if isinstance(p, dict) else None
        skills_applied = p.get("skills_applied") if isinstance(p, dict) else None
        if isinstance(tech_stack, list) and tech_stack:
            rel_props["tech_stack"] = [t for t in ( _norm_str(x) for x in tech_stack ) if t]
        if isinstance(skills_applied, list) and skills_applied:
            rel_props["skills_applied"] = [t for t in ( _norm_str(x) for x in skills_applied ) if t]
        # prune empty
        rel_props = {k: v for k, v in rel_props.items() if v not in (None, [], "")}

        ProjectManagement.link_by_name(cand_uid, title, rel_props=rel_props or None)
        summary["linked"]["projects"] += 1

    return summary


def get_candidate_full(uid: str) -> Dict[str, Any]:
    """
    Fetch a candidate and all linked features by uid.
        Returns:
      {
        "candidate": { "uid": str, "name": str, "location": Optional[str], "created_at": datetime, "updated_at": datetime },
        "job_titles":      List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
        "languages":       List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
        "majors":          List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
        "universities":    List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
        "skills":          List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
        "projects":        List[{"uid": str, "name": str, "rel_props": Dict[str, Any]}],
      }
    Raises:
      ValueError if the candidate does not exist.
    """
    # Lazy import to avoid circulars if any
    
    rows = CandidateRepository.get_by_uids(uids=[uid])
    if not rows:
        raise ValueError(f"Candidate uid not found: {uid}")

    cand = rows[0]
    
    # print(cand)
    
    result = {
        "candidate" : cand,
        "skills" : SkillManagement.list_for_candidate(uid),
        "job_title" : JobTitleManagement.list_for_candidate(uid),
        "major" : MajorManagement.list_for_candidate(uid),
        "university" : UniversityManagement.list_for_candidate(uid),
        "project" : ProjectManagement.list_for_candidate(uid)
    }
    
    return result


def topk_candidates_matching(features : Dict[str, Any] = None) -> Dict[str, Any]:
    pass

    