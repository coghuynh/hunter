# Hunter

Candidate Recommendation System for IT hiring, helping HR quickly find top matches using AI.

## Overview

<!-- <pre lang="markdown"> -->
<!-- 
## Project Structure

```text
hunter/
├─ pyproject.toml              # poetry/uv/pip-tools; khai báo deps
├─ .env                        # NEO4J_URI, NEO4J_USER, NEO4J_PASS, APP_ENV, LOG_LEVEL, ...
├─ .env.example
├─ .pre-commit-config.yaml     # black, isort, ruff, mypy, bandit
├─ Makefile                    # make run/api/test/lint/format/dev/up_weights/refresh_gds
├─ docker-compose.yml          # neo4j + app (nếu cần)
├─ README.md
└─ src/
   ├─ hunter/
   │  ├─ __init__.py
   │  ├─ config/
   │  │  ├─ __init__.py
   │  │  └─ settings.py        # load .env (pydantic-settings); logging config
   │  ├─ db/
   │  │  ├─ __init__.py
   │  │  ├─ neodb.py           # init neomodel (config.DATABASE_URL), db.cypher_query wrapper
   │  │  └─ constraints.py     # tạo index/constraint one-shot
   │  ├─ domain/               # lớp "mô hình"
   │  │  ├─ nodes.py           # Candidate, Skill, JobTitle, Education, Language, Project
   │  │  └─ relationships.py   # WeightEdge, UnweightEdge, Studied, HasSkill, Speak, WorkAs, WorkOn
   │  ├─ schema/               # Pydantic I/O models cho API
   │  │  ├─ candidate.py
   │  │  ├─ feature.py
   │  │  └─ recsys.py          # request/response cho recommend & shortest-path
   │  ├─ repository/           # truy vấn raw; đóng gói Cypher/ORM
   │  │  ├─ candidate_repo.py  # get/upsert candidate, attach features (MERGE)
   │  │  ├─ feature_repo.py    # upsert skill/lang/edu/project/title
   │  │  └─ graph_repo.py      # truy vấn GDS, shortest-path, projections
   │  ├─ services/             # business logic
   │  │  ├─ weighting.py       # chuẩn hoá weight cho Skill/Language/Education/Project/Title
   │  │  ├─ projection.py      # create/drop GDS projections (candFeature, candSkill, ...)
   │  │  ├─ recommendation.py  # related_candidates_by_shortest_path, shortest_path_between
   │  │  └─ ingestion.py       # ETL từ CV JSON → graph (upsert + link)
   │  ├─ api/                  # FastAPI
   │  │  ├─ __init__.py
   │  │  ├─ deps.py            # DI, dependency overrides, pagination
   │  │  ├─ app.py             # FastAPI instance, include_router
   │  │  └─ routers/
   │  │     ├─ candidates.py   # POST /candidates, GET /candidates/{uid}
   │  │     ├─ features.py     # POST /skills, /languages, ...
   │  │     ├─ recommend.py    # GET /candidates/{uid}/related?graph=&top_k=&max_hops=
   │  │     └─ ops.py          # POST /ops/recalc-weights, /ops/project-gds, /ops/refresh
   │  ├─ jobs/                 # batch/cron jobs
   │  │  ├─ recalc_weights.py  # chạy toàn bộ weighting.recalc_all_weights(...)
   │  │  └─ refresh_gds.py     # drop & project graphs
   │  ├─ utils/
   │  │  ├─ time.py            # years_since, decay
   │  │  ├─ text.py            # normalize, regex helpers
   │  │  └─ logging.py
   │  └─ cli/
   │     └─ main.py            # typer/click: hunter recalc-weights, hunter refresh-gds, ...
   └─ tests/
      ├─ conftest.py           # test fixtures (Neo4j test container / tmp db), seed data
      ├─ test_weighting.py
      ├─ test_recommendation.py
      ├─ test_repositories.py
      └─ test_api.py
```

</pre> -->


## Tech stack 

## Features 

## Installation / Setup

## Usage guide

## Layout / Screenshots


## License
Licensed under the Apache License, Version 2.0 – see the [LICENSE](LICENSE) file for details.

