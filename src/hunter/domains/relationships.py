from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class HasSkill(BaseModel):
    eid: Optional[str] = None
    level: Optional[int] = Field(default=None, ge=1)
    years: Optional[float] = Field(default=None, ge=0)
    weight: Optional[float] = Field(default=None, ge=0)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkedOn(BaseModel):
    eid: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Speaks(BaseModel):
    eid: Optional[str] = None
    level: Optional[int] = Field(default=None, ge=1)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HasTitle(BaseModel):
    eid: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MajoredIn(BaseModel):
    eid: Optional[str] = None
    degree: Optional[str] = None
    gpa: Optional[float] = Field(default=None, ge=0)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GraduatedFrom(BaseModel):
    eid: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=1900)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

