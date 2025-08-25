from neomodel import (
    StructuredNode, StringProperty,
    DateTimeProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom
)

from domains.relationships import *

class Candidate(StructuredNode):
    uid = UniqueIdProperty()
    name = StringProperty(index=True)
    location = StringProperty(index=True, required=False)
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    studied   = RelationshipFrom('Education', 'STUDIED', model=Studied)
    job_titles= RelationshipFrom('JobTitle', 'WORK_AS', model=WorkAs)
    languages = RelationshipFrom('Language', 'SPEAK', model=Speak)
    skills    = RelationshipFrom('Skill', 'HAS_SKILL', model=HasSkill)
    projects  = RelationshipFrom('Project', 'WORK_ON', model=WorkOn)

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