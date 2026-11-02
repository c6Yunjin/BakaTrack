"""Loads the two SAMPLE (fake) datasets into the database. Safe to run twice."""
from database import db
from modules.csv_upload import upload_dataset

A = "Padre Garcia (SAMPLE)"
B = "SAMPLE_Dataset_B"
SOURCE = "SAMPLE (fake) data made by scripts in data/sample"

db.init_db()
names = {d["name"]: d["id"] for d in db.list_datasets()}

if A not in names:
    others = [d for d in db.list_datasets() if d["name"] != B]
    if others:                                   # rename the dataset we already have
        conn = db.get_connection()
        conn.execute("UPDATE datasets SET name = ? WHERE id = ?", (A, others[0]["id"]))
        conn.commit()
        conn.close()
    else:
        print(upload_dataset("data/sample/SAMPLE_cattle_data.csv", A, SOURCE))
if B not in names:
    print(upload_dataset("data/sample/SAMPLE_dataset_B.csv", B, SOURCE))

for d in db.list_datasets():
    print(d["id"], d["name"], "|", len(db.get_records(d["id"])), "records")
