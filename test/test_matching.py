import os
import time
from datetime import datetime

import pytest
from neomodel import config

from hunter.db import db_instance as db

# -----------------------------
# Global/Session-level fixtures
# -----------------------------

@pytest.fixture(scope="session", autouse=True)
def configure_neo4j():
    """
    Configure Neo4j connection for test session and ensure a clean DB
    before and after all tests.
    """
    # Allow .env to override if present
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("neo4j://", "bolt://")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD", "test20032004")

    if uri.startswith("bolt://") or uri.startswith("bolt+s://"):
        scheme, rest = uri.split("://", 1)
        database_url = f"{scheme}://{user}:{pwd}@{rest}"
    else:
        database_url = f"bolt://{user}:{pwd}@localhost:7687"

    config.DATABASE_URL = database_url
    # small delay to make sure config is set (mostly useful in CI)
    time.sleep(0.2)

    # Ensure a clean DB before session
    db.cypher_query("MATCH (n) DETACH DELETE n")

    yield

    # Cleanup after session
    db.cypher_query("MATCH (n) DETACH DELETE n")


@pytest.fixture(autouse=True)
def clean_between_tests():
    db.cypher_query("MATCH (n) DETACH DELETE n")
    yield
    db.cypher_query("MATCH (n) DETACH DELETE n")

