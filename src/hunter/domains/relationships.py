from neomodel import (
    StructuredNode, StructuredRel, StringProperty, FloatProperty,
    DateTimeProperty, UniqueIdProperty, RelationshipTo, RelationshipFrom, db
)
from datetime import datetime
import re

class WeightEdge(StructuredRel):
    eid = UniqueIdProperty()
    weight = FloatProperty(default=1.0)   
    cost   = FloatProperty(default=1.0)   
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    def set_weight(self, w: float):
        """
        Normalize weight and cost (cost = 1 / max(w, eps)) for find shortest path by Dijkstra.
        """
        eps = 1e-6
        w = max(float(w), 0.0)
        self.weight = w
        self.cost = 1.0 / max(w, eps) if w > 0 else 1.0  
        self.updated_at = datetime.utcnow()
        self.save()

class UnweightEdge(StructuredRel):
    eid = UniqueIdProperty()
    _weight = FloatProperty(default=1.0)
    cost = FloatProperty(default=1.0)  
    created_at = DateTimeProperty(default_now=True)
    updated_at = DateTimeProperty(default_now=True)

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, _):
        return

class Studied(WeightEdge):
    DEGREE_SCORES = {
        "high_school": 2.0, "diploma": 3.0, "associate": 4.0,
        "bachelor": 6.0, "bachelor_honours": 6.5,
        "master": 8.0, "mphil": 8.5, "professional_master": 8.5,
        "professional_doctorate": 9.5, "phd": 10.0, "unknown": 0.0
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

    gpa = FloatProperty(required=False)
    degree = StringProperty(required=False)
    fromDate = DateTimeProperty(required=False)
    toDate = DateTimeProperty(required=False)

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

class LearnOn(WeightEdge):
    pass 

# Self-relationship edges for feature similarity
class SimilarSkill(WeightEdge):
    """
    Self-relationship between Skill nodes, e.g., (Skill)-[:SIMILAR_SKILL {weight, cost}]->(Skill).
    Use `set_weight(similarity)` where similarity ∈ [0,1].
    """
    pass

class SimilarLanguage(WeightEdge):
    """
    Self-relationship between Language nodes, e.g., (Language)-[:SIMILAR_LANGUAGE {weight, cost}]->(Language).
    """
    pass

class SimilarJobTitle(WeightEdge):
    """
    Self-relationship between JobTitle nodes, e.g., (JobTitle)-[:SIMILAR_TITLE {weight, cost}]->(JobTitle).
    """
    pass

