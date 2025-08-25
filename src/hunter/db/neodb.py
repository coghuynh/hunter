from neomodel import (
    config, db
)

from hunter.config import (
    NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
)

config.DATABASE_URL = f"bolt://{NEO4J_USER}:{NEO4J_PASSWORD}@{NEO4J_URI}"

def run_cyper(query: str, params: dict = None): 
    results, meta = db.cypher_query(query, params)
    return results, meta