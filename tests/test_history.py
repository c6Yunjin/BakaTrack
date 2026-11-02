import sqlite3

import pandas as pd

from app import app as flask_app
from database import db


def make_dataset(tmp_path, monkeypatch, name):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-15"], "head_count": [10],
                       "total_kilos": [1000.0], "price_per_kilo": [100.0]})
    return db.create_dataset_with_records(name, "test", df)


CHART = {"type": "line", "labels": ["Jan 2026", "Feb 2026"], "values": [100.5, None],
         "metric": "price_per_kilo", "label": "price per kilo"}


def test_history_keeps_chart_and_stays_per_dataset(tmp_path, monkeypatch):
    a = make_dataset(tmp_path, monkeypatch, "A")
    b = make_dataset(tmp_path, monkeypatch, "B")
    db.save_chat_log(a, "question A", "show_chart", 0.9, "answer A", CHART)
    db.save_chat_log(b, "question B", "greeting", 0.99, "answer B")
    history_a = db.get_chat_history(a)
    assert [h["message"] for h in history_a] == ["question A"]
    assert history_a[0]["chart"]["values"] == [100.5, None]      # the gap survives
    assert [h["message"] for h in db.get_chat_history(b)] == ["question B"]


def test_clear_hides_only_that_dataset_and_keeps_the_rows(tmp_path, monkeypatch):
    a = make_dataset(tmp_path, monkeypatch, "A")
    b = make_dataset(tmp_path, monkeypatch, "B")
    db.save_chat_log(a, "question A", "greeting", 0.9, "answer A")
    db.save_chat_log(b, "question B", "greeting", 0.9, "answer B")
    db.clear_chat_history(a)
    assert db.get_chat_history(a) == []
    assert len(db.get_chat_history(b)) == 1
    conn = db.get_connection()
    total = conn.execute("SELECT COUNT(*) AS n FROM chat_logs").fetchone()["n"]
    conn.close()
    assert total == 2                                            # nothing was deleted


def test_history_and_clear_routes(tmp_path, monkeypatch):
    a = make_dataset(tmp_path, monkeypatch, "A")
    db.save_chat_log(a, "hello", "greeting", 0.99, "Hello!")
    client = flask_app.test_client()
    data = client.get("/api/datasets/%d/history" % a).get_json()
    assert len(data["messages"]) == 1
    assert client.post("/api/datasets/%d/clear" % a).status_code == 200
    assert client.get("/api/datasets/%d/history" % a).get_json()["messages"] == []
    assert client.get("/api/datasets/99999/history").status_code == 404
    assert client.post("/api/datasets/99999/clear").status_code == 404


def test_old_database_is_upgraded_without_losing_rows(tmp_path, monkeypatch):
    path = str(tmp_path / "old.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE chat_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, dataset_id INTEGER,"
                 " message TEXT, detected_intent TEXT, confidence REAL, response TEXT,"
                 " timestamp TEXT DEFAULT CURRENT_TIMESTAMP)")
    conn.execute("INSERT INTO chat_logs (dataset_id, message, response) VALUES (1, 'old q', 'old a')")
    conn.commit()
    conn.close()
    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    history = db.get_chat_history(1)
    assert history[0]["message"] == "old q"
    assert history[0]["chart"] is None
