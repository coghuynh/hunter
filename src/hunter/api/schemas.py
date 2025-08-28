from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, UUID4, conint, field_validator
from datetime import datetime

# ---------- Shared types ----------
SkillLevel = Literal["beginner", "intermediate", "advanced", "expert"]
LangLevel = Literal["A1", "A2", "B1", "B2", "C1", "C2", "native"]

class Salary(BaseModel):
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    min: Optional[float] = None
    max: Optional[float] = None

class SkillItem(BaseModel):
    name: str
    level: Optional[SkillLevel] = None
    years: Optional[float] = Field(default=None, ge=0)

class LanguageItem(BaseModel):
    name: Optional[str] = None
    level: Optional[LangLevel] = None

class EducationItem(BaseModel):
    university: Optional[str] = None
    major: Optional[str] = None
    degree: Optional[
        Literal[
            "high_school","diploma","associate","bachelor","bachelor_honours",
            "master","mphil","professional_master","professional_doctorate","phd","unknown"
        ]
    ] = None
    gpa: Optional[float] = None

# ---------- Candidate ----------
class Candidate(BaseModel):
    id: UUID4
    name: str
    headline: Optional[str] = None
    location: Optional[str] = None
    remote_ok: Optional[bool] = None
    salary_expectation: Optional[Salary] = None
    experience_years: Optional[float] = Field(default=None, ge=0)
    skills: Optional[List[SkillItem]] = None
    job_titles: Optional[List[str]] = None
    languages: Optional[List[LanguageItem]] = None
    education: Optional[List[EducationItem]] = None
    projects: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CandidateCreate(Candidate):
    id: Optional[UUID4] = Field(default=None)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CandidateUpdate(BaseModel):
    # Partial: any field may appear
    name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    remote_ok: Optional[bool] = None
    salary_expectation: Optional[Salary] = None
    experience_years: Optional[float] = Field(default=None, ge=0)
    skills: Optional[List[SkillItem]] = None
    job_titles: Optional[List[str]] = None
    languages: Optional[List[LanguageItem]] = None
    education: Optional[List[EducationItem]] = None
    projects: Optional[List[str]] = None
    tags: Optional[List[str]] = None

# ---------- Match ----------
class MustHaveSkill(BaseModel):
    name: str
    min_level: Optional[SkillLevel] = None
    min_years: Optional[float] = Field(default=None, ge=0)

class MustHaveLang(BaseModel):
    name: Optional[str] = None
    min_level: Optional[LangLevel] = None

class MustHave(BaseModel):
    skills: Optional[List[MustHaveSkill]] = None
    languages: Optional[List[MustHaveLang]] = None
    degrees: Optional[List[str]] = None
    job_titles_any: Optional[List[str]] = None
    location_any: Optional[List[str]] = None
    remote_ok: Optional[bool] = None
    salary_max: Optional[float] = None

class NiceSkill(BaseModel):
    name: str
    weight: Optional[float] = 1.0
    prefer_min_years: Optional[float] = 0.0
    prefer_level: Optional[SkillLevel] = None

class NiceToHave(BaseModel):
    skills: Optional[List[NiceSkill]] = None
    job_titles: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    education: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    location_preference: Optional[str] = None

class Weights(BaseModel):
    skills: Optional[float] = 0.6
    job_titles: Optional[float] = 0.1
    languages: Optional[float] = 0.05
    education: Optional[float] = 0.1
    keywords: Optional[float] = 0.1
    location: Optional[float] = 0.05

class MatchRequest(BaseModel):
    top_k: conint(ge=1, le=200) = 20
    must_have: Optional[MustHave] = None
    nice_to_have: Optional[NiceToHave] = None
    weights: Optional[Weights] = None
    explain: Optional[bool] = True
    include_fields: Optional[List[str]] = None
    cursor: Optional[str] = None

    @field_validator("include_fields")
    @classmethod
    def ensure_unique_fields(cls, v):
        if v:
            return list(dict.fromkeys(v))
        return v

class ReasonItem(BaseModel):
    kind: Literal["skill", "job_title", "language", "education", "keyword", "location"]
    detail: str
    weight: float
    contribution: float

class MatchResponseItem(BaseModel):
    candidate: Dict[str, Any]
    score: float
    reasons: Optional[List[ReasonItem]] = None

class MatchResponse(BaseModel):
    top_k: int
    items: List[MatchResponseItem]
    next_cursor: Optional[str] = None

# ---------- Listings / Bulk ----------
class CandidateListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Candidate]

class BulkItemError(BaseModel):
    index: int
    message: str

class BulkUpsertResponse(BaseModel):
    inserted: int
    updated: int
    errors: List[BulkItemError]