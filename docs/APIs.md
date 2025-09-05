# Hunter APIs

Base URL: `/v1` (adjust if your Flask app prefixes differently)

Content-Type: `application/json` for all requests and responses.

> Error format (all endpoints):  
> `{"error": "<message>"}`

---

## 1) Create/Upsert Candidate from a Parsed Resume

**Endpoint**  
`POST /candidates/from_resume`

**Description**  
Ingest a parsed resume JSON, create (or upsert) a `Candidate`, and link related entities (skills, languages, job titles, majors, universities, projects, …).

**Request Body**
```json
{
  "name": "Jane Doe",
  "job_title": ["Backend Engineer", "Data Engineer"],
  "foreign_languages": ["English", "Japanese"],
  "majors": ["Computer Science"],
  "graduated_from": ["HUST"],
  "skills": [
    {"skill": "Python", "mastery": "expert"},
    {"skill": "Neo4j", "mastery": "intermediate"}
  ],
  "projects": [
    {
      "title": "Realtime ETL",
      "description": "Kafka + Spark streaming pipeline",
      "role": "Developer",
      "tech_stack": ["Kafka", "Spark", "Airflow"],
      "skills_applied": ["Python", "SQL"],
      "duration": "2023-01 to 2023-05",
      "objective": "Low-latency ingestion",
      "contribution": "Authored Spark jobs",
      "impact": "Latency < 2s",
      "collaboration_type": "Team of 4",
      "scale": "100K msg/min"
    }
  ]
}
```


## 2) Get Full Candidate (with Linked Features)

**Endpoint**

`GET /candidates/<uid>/full`

Description
Return the candidate and all linked entities (skills, languages, titles, education, projects, …).
Dates are ISO-8601 strings (internally converted via jsonify_safe).

**Params**

uid – Candidate UID (UUID string)

**Reponse**

- `200 OK`

```json
{
  "uid": "2f6a5b8e-1c5c-4c0c-92b0-0a9a2f3d4e56",
  "name": "Jane Doe",
  "location": "Hanoi",
  "created_at": "2025-08-27T13:21:05.123456",
  "updated_at": "2025-08-27T13:21:05.123456",
  "skills": [
    {"name": "Python", "mastery": "expert", "weight": 0.9},
    {"name": "Neo4j", "mastery": "intermediate", "weight": 0.6}
  ],
  "languages": ["English", "Japanese"],
  "job_titles": ["Backend Engineer", "Data Engineer"],
  "education": {
    "majors": ["Computer Science"],
    "universities": ["HUST"]
  },
  "projects": [
    {
      "title": "Realtime ETL",
      "tech_stack": ["Kafka", "Spark", "Airflow"],
      "impact": "Latency < 2s"
    }
  ]
}
```


## 3) Search Candidates (Filter Only)

Endpoint

`POST /candidates/search`

Description

Filter candidates by required features without computing scores. Use this when you only need matching, not ranking.

Request Body

```json
{
  "must_have": {
    "skills": [
      {"name": "python", "min_level": "advanced", "min_years": 2}
    ],
    "languages": [
      {"name": "english", "min_level": "B2"}
    ],
    "job_titles_any": ["data engineer", "ml engineer"],
    "location_any": ["ho chi minh city", "remote"],
    "remote_ok": true,
    "salary_max": 2000
  },
  "include_fields": ["uid", "name", "location", "experience_years", "salary_max"],
  "skip": 0,
  "limit": 50
}
```

Response

```json
{
  "items": [
    {"uid": "...", "name": "Alice", "location": "HCMC", "experience_years": 4, "salary_max": 1500},
    {"uid": "...", "name": "Bob",   "location": "Remote", "experience_years": 3, "salary_max": 1200}
  ],
  "skip": 0,
  "limit": 50
}
```
