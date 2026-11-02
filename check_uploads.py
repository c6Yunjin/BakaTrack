"""TC-16 and TC-17: upload tests through the real Flask route. Saves evidence."""
import json
import os

import config
from app import app
from database import db

GOOD = "data/sample/SAMPLE_cattle_data.csv"
BAD = "data/sample/bad_example.csv"


def count():
    return len(db.list_datasets())


db.init_db()
client = app.test_client()
results = {}

# TC-16: a valid CSV adds one new dataset
before = count()
with open(GOOD, "rb") as f:
    reply = client.post("/api/upload", data={"name": "TC16 Test Upload", "file": (f, "good.csv")},
                        content_type="multipart/form-data")
body = reply.get_json()
results["TC-16"] = {"status": reply.status_code, "datasets_before": before, "datasets_after": count(),
                    "passed": reply.status_code == 200 and count() == before + 1}
if "dataset_id" in body:
    db.delete_dataset(body["dataset_id"])          # clean up so the demo stays tidy

# TC-17: a bad CSV shows clear errors and saves nothing
before = count()
with open(BAD, "rb") as f:
    reply = client.post("/api/upload", data={"name": "TC17 Bad Upload", "file": (f, "bad.csv")},
                        content_type="multipart/form-data")
errors = reply.get_json().get("errors", [])
results["TC-17"] = {"status": reply.status_code, "errors_shown": errors[:5], "datasets_before": before,
                    "datasets_after": count(),
                    "passed": reply.status_code == 400 and len(errors) > 0 and count() == before}

for name, r in results.items():
    print(name, "PASS" if r["passed"] else "FAIL", r)
out = os.path.join(config.EVIDENCE_DIR, "upload_tests.json")
json.dump(results, open(out, "w", encoding="utf-8"), indent=2)
print("Saved:", out)
