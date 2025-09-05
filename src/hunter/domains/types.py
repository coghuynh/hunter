from __future__ import annotations
from enum import Enum


class NodeLabel(str, Enum):
    Candidate = "Candidate"
    Skill = "Skill"
    Project = "Project"
    Language = "Language"
    JobTitle = "JobTitle"
    Major = "Major"
    University = "University"


class RelType(str, Enum):
    HAS_SKILL = "HAS_SKILL"
    WORKED_ON = "WORKED_ON"
    SPEAKS = "SPEAKS"
    HAS_TITLE = "HAS_TITLE"
    MAJORED_IN = "MAJORED_IN"
    GRADUATED_FROM = "GRADUATED_FROM"

