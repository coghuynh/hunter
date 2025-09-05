from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class Candidate(BaseModel):
    uid: Optional[str] = None
    name: str
    location: Optional[str] = None
    headline: Optional[str] = None
    remote_ok: Optional[bool] = None
    experience_years: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Skill(BaseModel):
    uid: Optional[str] = None
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class JobTitle(BaseModel):
    uid: Optional[str] = None
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class University(BaseModel):
    uid: Optional[str] = None
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Major(BaseModel):
    uid: Optional[str] = None
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Project(BaseModel):
    uid: Optional[str] = None
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Language(BaseModel):
    uid: Optional[str] = None
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
