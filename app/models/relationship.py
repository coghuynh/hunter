from neomodel import (
    StructuredRel, FloatProperty, StringProperty, DateTimeProperty,
    UniqueIdProperty
)
import typing
import re
from datetime import datetime

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
    def weight(self, val):
        pass
    
    
class Studied(WeightEdge):
    

    # score for each level of education
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
        "unknown": 0.0
    }

    # normalize for scoring 
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
    
    _gpa = FloatProperty()
    _degree = StringProperty()
    _fromDate = DateTimeProperty(default_now=True)
    _toDate = DateTimeProperty(default_now=True)
    
    @property
    def GPA(self) -> float:
        return self._gpa
    
    @GPA.setter
    def GPA(self, value : typing.Optional[float]) -> None:
        
        if value > 4.0 or value < 0.0:
            self._gpa = 0.0
            raise ValueError("Invalid GPA. Should in range 0.0 to 4.0 !")
        
        self._gpa = (value if value else 0.0)
        
    @property
    def degree(self) -> str:
        return self._degree
    
    @degree.setter
    def degree(self, deg : typing.Optional[str]) -> None:
        if deg is None:
            self._degree = "unknown"
        self._degree = deg
        
    @property
    def fromDate(self) -> datetime:
        return self._fromDate
    
    @fromDate.setter
    def fromDate(self, time : datetime | None) -> None:
        if time is None:
            return
        self._fromDate = time
        
    @property
    def toDate(self) -> datetime:
        return self._toDate
    
    @toDate.setter
    def toDate(self, time : datetime | None) -> None:
        if time is None:
            return
        self._toDate = time
        
    def degree_to_score(self, deg : str | None = None) -> float: 
        if deg is None:
            return 0.0
        deg = deg.lower().strip()
        deg = deg.replace("'", "").replace("-", "")
        for pattern, canon in self.DEGREE_ALIASES:
            if re.search(pattern, deg):
                return self.DEGREE_SCORES[canon]
        return self.DEGREE_SCORES["unknow"]
        
        
    
    
        

class WorkAs(UnweightEdge):
    pass

class Speak(WeightEdge):
    pass 

class HasSkill(WeightEdge):
    pass 

class WorkOn(WeightEdge):
    pass