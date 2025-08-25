

from hunter.repository.candidate_repo import (
    upsert_candidate, 
    list_candidates
)

from neomodel import config
# from hunter.config import *

def main():
    # print(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    # print(config.DATABASE_URL)
    # pass
    print(upsert_candidate(
        "Alice"
    ))
    
    for c in list_candidates():
        print(c)


if __name__ == "__main__":
    main()