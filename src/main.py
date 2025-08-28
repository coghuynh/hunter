import json
from pathlib import Path

from hunter.services.candidates import add_candidate_from_resume

DATA_PATH = Path("./data/resumes.json")

def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a list of resume objects in the JSON file")

    n = min(10, len(data))
    print(f"Ingesting {n} candidates from {DATA_PATH} ...")

    summaries = []
    for i, resume in enumerate(data[:n], start=1):
        try:
            summary = add_candidate_from_resume(resume)
            summaries.append(summary)
            print(f"[{i}/{n}] OK  -> candidate_uid={summary['candidate_uid']} linked={summary['linked']}")
        except Exception as e:
            print(f"[{i}/{n}] FAIL -> {e}")

    print("\nDone. Summary:")
    ok = sum(1 for s in summaries if s)
    print(f"Inserted {ok}/{n} candidates successfully.")

if __name__ == "__main__":
    main()