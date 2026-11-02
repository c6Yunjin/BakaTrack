# Step 1 check: database, CSV upload, and rejection of bad files.
import os
from database.db import init_db, get_dataset_id, delete_dataset, get_records
from modules.csv_upload import upload_dataset, validate_csv
from config import BASE_DIR

SAMPLE = os.path.join(BASE_DIR, "data", "sample", "SAMPLE_cattle_data.csv")
BAD = os.path.join(BASE_DIR, "data", "sample", "bad_example.csv")
NAME = "SAMPLE - Demo Market"


def test_valid_upload_and_read():
    init_db()
    old_id = get_dataset_id(NAME)
    if old_id:
        delete_dataset(old_id)
    dataset_id, errors = upload_dataset(SAMPLE, NAME, "SAMPLE data, not real")
    assert errors == []
    assert len(get_records(dataset_id)) > 0


def test_missing_columns_rejected():
    df, errors = validate_csv(BAD)
    assert df is None and len(errors) > 0
    print(errors)


def test_bad_values_rejected(tmp_path):
    f = tmp_path / "bad.csv"
    f.write_text("date,head_count,total_kilos,price_per_kilo\n2026/01/12,-5,abc,100\n")
    df, errors = validate_csv(str(f))
    assert df is None
    assert len(errors) >= 3     # bad date, negative, not a number
