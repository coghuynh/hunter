from dotenv import load_dotenv
import os
from neomodel import config, db
from models import *

load_dotenv()

config.DATABASE_URL = f'bolt://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}@localhost:7687'  # default

db.cypher_query("MATCH (n) DETACH DELETE n")

edu = Education(school="HCMUT", major="Computer Science").save()
hip = Skill(name="HIP").save()
gpu_title = JobTitle(title="GPU Engineer").save()
jp = Language(name="Japanese").save()
proj = Project(name="GraphRAG Recruiter", domain="Recruiting").save()
alice = Candidate(name="Alice Nguyen", location="HCM").save()


edu.candidates.connect(alice, {
    "gpa": 3.7, "degree": "Master of Computer Science",
    "fromDate": datetime(2020, 9, 1), "toDate": datetime(2022, 6, 30),
    "weight": 8.0
})
hip.candidates.connect(alice, {"weight": 8.5})
gpu_title.candidates.connect(alice)              
proj.candidates.connect(alice, {"weight": 9.0})



