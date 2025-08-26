from neomodel import (
    config
)

from hunter.config import (
    NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER
)

config.DATABASE_URL = f"bolt://{NEO4J_USER}:{NEO4J_PASSWORD}@{NEO4J_URI}"

from neomodel import db
from typing import Dict, Any

db_instance = db

def run(q: str, params: Dict[str, Any]):
    rows, _ = db_instance.cypher_query(q, params)
    return rows