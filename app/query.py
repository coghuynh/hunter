from models import *
from neomodel import config
import os
from dotenv import load_dotenv

load_dotenv()

config.DATABASE_URL = f'bolt://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}@localhost:7687'  # default


edu = Education.nodes.get(school="HCMUT")
results = []
for c in edu.candidates.all():
    rel = edu.candidates.relationship(c)
    print(rel.gpa)
    if rel.gpa and rel.gpa >= 3.5:
        results.append((c.name, rel.degree, rel.gpa))

print(results)
