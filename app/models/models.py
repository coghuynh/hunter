from neomodel import (
    StructuredNode, StructuredRel, StringProperty, FloatProperty,
    DateTimeProperty, UniqueIdProperty,
    RelationshipTo, RelationshipFrom
)
from datetime import datetime
import typing
import re

class WeightEdge(StructuredRel):
    eid = UniqueIdProperty()
    weight = FloatProperty()

class UnweightEdge(StructuredRel):
    eid = UniqueIdProperty()
    _weight = FloatProperty(default=1.0)

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, _):
        return

class Studied(WeightEdge):
    DEGREE_SCORES = {
        "high_school": 2.0,
        "diploma": 3.0,
        "associate": 4.0,
        "bachelor": 6.0,
        "bachelor_honours": 6.5,
        "master": 8.0,
        "mphil": 8.5,
        "professional_master": 8.5,
        "professional_doctorate": 9.5,
        "phd": 10.0,
        "unknown": 0.0,
    }

    DEGREE_ALIASES = {
        r"(high\s*school|secondary|hs diploma)": "high_school",
        r"(certificate|cert|pgcert|postgraduate\s+certificate|pgdip|postgraduate\s+diploma)": "diploma",
        r"(associate|aa|as|aas|abdus|abus|afa|ae)\b": "associate",
        r"(bachelor|ba|bs|bsc|b\.s\.|b\.a\.|beng|barch|bed|llb|bn|bsn|bcs|bfa|bsw)\b": "bachelor",
        r"(honours|honors|hons)": "bachelor_honours",
        r"(master|ma|ms|msc|m\.s\.|m\.a\.|meng|med|msw|mca|mn|msn)\b": "master",
        r"(mphil)\b": "mphil",
        r"(mba|mpp|mpa|mph|llm|march)\b": "professional_master",
        r"(phd|dphil|scd|dsc)\b": "phd",
        r"(md|jd|do|dds|dmd|pharmd|dvm|engd|dba|edd|drph)\b": "professional_doctorate",
    }

    gpa = FloatProperty()
    degree = StringProperty()
    fromDate = DateTimeProperty()
    toDate = DateTimeProperty()

    def degree_to_score(self, deg: str | None = None) -> float:
        if not deg:
            return self.DEGREE_SCORES["unknown"]
        norm = deg.lower().strip().replace("'", "").replace("-", " ")
        for pattern, canon in self.DEGREE_ALIASES.items():
            if re.search(pattern, norm):
                return self.DEGREE_SCORES.get(canon, self.DEGREE_SCORES["unknown"])
        return self.DEGREE_SCORES["unknown"]

class WorkAs(UnweightEdge):
    pass

class Speak(WeightEdge):
    pass

class HasSkill(WeightEdge):
    pass

class WorkOn(WeightEdge):
    pass

class Candidate(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(index=True)
    location = StringProperty(index=True, required=False)

    studied = RelationshipFrom('Education', 'STUDIED', model=Studied)
    job_titles = RelationshipFrom('JobTitle', 'WORK_AS', model=WorkAs)
    languages = RelationshipFrom('Language', 'SPEAK', model=Speak)
    skills = RelationshipFrom('Skill', 'HAS_SKILL', model=HasSkill)
    projects = RelationshipFrom('Project', 'WORK_ON', model=WorkOn)

class Education(StructuredNode):
    uid = UniqueIdProperty()
    school = StringProperty(index=True)
    major = StringProperty(index=True, required=False)
    country = StringProperty(required=False)

    candidates = RelationshipTo(Candidate, 'STUDIED', model=Studied)

class JobTitle(StructuredNode):
    uid = UniqueIdProperty()
    title = StringProperty(unique_index=True)

    candidates = RelationshipTo(Candidate, 'WORK_AS', model=WorkAs)

class Language(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True)

    candidates = RelationshipTo(Candidate, 'SPEAK', model=Speak)

class Skill(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(unique_index=True)

    candidates = RelationshipTo(Candidate, 'HAS_SKILL', model=HasSkill)

class Project(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(index=True)
    domain = StringProperty(required=False)
    objective = StringProperty(required=False)

    candidates = RelationshipTo(Candidate, 'WORK_ON', model=WorkOn)