import pandas as pd
import pytest

import app as app_module
from database import db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))   # a fresh temporary database
    db.init_db()
    return app_module.app.test_client()


def make_dataset(name, kilos):
    df = pd.DataFrame({"date": ["2026-06-10", "2026-06-20"], "head_count": [10, 10],
                       "total_kilos": [kilos, kilos], "price_per_kilo": [100.0, 100.0]})
    return db.create_dataset_with_records(name, "test", df)


def test_datasets_route_lists_tabs(client):
    make_dataset("Tab A", 1000)
    data = client.get("/api/datasets").get_json()
    assert len(data) == 1 and data[0]["name"] == "Tab A"


def test_unknown_tab_is_rejected(client):
    res = client.post("/api/chat", json={"dataset_id": 999, "message": "hello"})
    assert res.status_code == 404


def test_tabs_stay_separate(client):
    # TC-15: same question in two tabs, each answers from its own dataset
    a = make_dataset("Tab A", 1000)     # June total = 2,000 kg
    b = make_dataset("Tab B", 5000)     # June total = 10,000 kg
    question = "How many total kilos in June 2026?"
    reply_a = client.post("/api/chat", json={"dataset_id": a, "message": question}).get_json()["reply"]
    reply_b = client.post("/api/chat", json={"dataset_id": b, "message": question}).get_json()["reply"]
    assert "2,000 kg" in reply_a
    assert "10,000 kg" in reply_b
    assert reply_a != reply_b


def test_upload_without_file_is_rejected(client):
    res = client.post("/api/upload", data={"name": "X"})
    assert res.status_code == 400


def test_dataset_info_route(client):
    ds = make_dataset("SAMPLE Tab", 1000)
    info = client.get("/api/datasets/%d/info" % ds).get_json()
    assert info["records"] == 2
    assert info["first_date"] == "2026-06-10"
    assert info["last_date"] == "2026-06-20"
    assert info["is_sample"] is True
    assert client.get("/api/datasets/999/info").status_code == 404
