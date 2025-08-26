from hunter.db.neodb import run_cyper
from neomodel import config

QUERIES = [

    # ---------- UNIQUE by uid ----------
    "CREATE CONSTRAINT candidate_uid IF NOT EXISTS "
    "FOR (n:Candidate) REQUIRE n.uid IS UNIQUE",
    
    "CREATE CONSTRAINT jobtitle_uid IF NOT EXISTS "
    "FOR (n:JobTitle) REQUIRE n.uid IS UNIQUE",

    "CREATE CONSTRAINT language_uid IF NOT EXISTS "
    "FOR (n:Language) REQUIRE n.uid IS UNIQUE",
        
    "CREATE CONSTRAINT university_uid IF NOT EXISTS "
    "FOR (n:University) REQUIRE n.uid IS UNIQUE",

    "CREATE CONSTRAINT major_uid IF NOT EXISTS "
    "FOR (n:Major) REQUIRE n.uid IS UNIQUE",

    # "CREATE CONSTRAINT degree_uid IF NOT EXISTS "
    # "FOR (n:Degree) REQUIRE n.uid IS UNIQUE",

    "CREATE CONSTRAINT skill_uid IF NOT EXISTS "
    "FOR (n:Skill) REQUIRE n.uid IS UNIQUE",

    "CREATE CONSTRAINT project_uid IF NOT EXISTS "
    "FOR (n:Project) REQUIRE n.uid IS UNIQUE",

    # ---------- UNIQUE dictionaries ----------
    "CREATE CONSTRAINT language_name_unique IF NOT EXISTS "
    "FOR (n:Language) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT skill_name_unique IF NOT EXISTS "
    "FOR (n:Skill) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT jobtitle_title_unique IF NOT EXISTS "
    "FOR (n:JobTitle) REQUIRE n.title IS UNIQUE",
    
    "CREATE CONSTRAINT university_name_unique IF NOT EXISTS "
    "FOR (n:University) REQUIRE n.name IS UNIQUE",

    "CREATE CONSTRAINT major_name_unique IF NOT EXISTS "
    "FOR (n:Major) REQUIRE n.name IS UNIQUE",

    # "CREATE CONSTRAINT degree_name_unique IF NOT EXISTS "
    # "FOR (n:Degree) REQUIRE n.name IS UNIQUE",

    # ---------- INDEX for lookups ----------
    "CREATE INDEX candidate_name IF NOT EXISTS "
    "FOR (n:Candidate) ON (n.name)",

    "CREATE INDEX candidate_location IF NOT EXISTS "
    "FOR (n:Candidate) ON (n.location)",

    "CREATE INDEX project_name IF NOT EXISTS "
    "FOR (n:Project) ON (n.name)",
    
    "CREATE INDEX university_name_idx IF NOT EXISTS FOR (n:University) ON (n.name)",
    "CREATE INDEX major_name_idx IF NOT EXISTS FOR (n:Major) ON (n.name)",
    # "CREATE INDEX degree_name_idx IF NOT EXISTS FOR (n:Degree) ON (n.name)",

    # ---------- RELATIONSHIP PROPERTY EXISTENCE ----------
    # WeightEdge & UnweightEdge in your schema always set r.cost
    # "CREATE CONSTRAINT rel_cost_studied IF NOT EXISTS "
    # "FOR ()-[r:STUDIED]-() REQUIRE r.cost IS NOT NULL",

    # "CREATE CONSTRAINT rel_cost_speak IF NOT EXISTS "
    # "FOR ()-[r:SPEAK]-() REQUIRE r.cost IS NOT NULL",

    # "CREATE CONSTRAINT rel_cost_has_skill IF NOT EXISTS "
    # "FOR ()-[r:HAS_SKILL]-() REQUIRE r.cost IS NOT NULL",

    # "CREATE CONSTRAINT rel_cost_work_on IF NOT EXISTS "
    # "FOR ()-[r:WORK_ON]-() REQUIRE r.cost IS NOT NULL",
]


def create_constraints(verbose: bool = True):
    for q in QUERIES:
        run_cyper(q)
        if verbose:
            print(f"{q} : SUCESS\n")


if __name__ == "__main__":
    create_constraints()
    # print(config.DATABASE_URL)