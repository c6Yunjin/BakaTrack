import pandas as pd

from app import app as flask_app
from database import db
from modules import chat_engine, data_view
from modules import response_builder as rb


def make_dataset(tmp_path, monkeypatch, name, dates, price=100.0):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    n = len(dates)
    df = pd.DataFrame({"date": dates, "head_count": [10] * n,
                       "total_kilos": [1000.0] * n, "price_per_kilo": [price] * n})
    return db.create_dataset_with_records(name, "test", df)


THREE = ["2026-01-10", "2026-01-20", "2026-02-05"]


def test_requests_match():
    assert data_view.match("Show the data") == "show_data"
    assert data_view.match("show me the data please") == "show_data"
    assert data_view.match("ipakita ang datos") == "show_data"
    assert data_view.match("ipakita mo nga ang datos") == "show_data"
    assert data_view.match("dataset") == "show_data"
    assert data_view.match("Show RAW records!") == "show_data_raw"


def test_real_questions_are_never_taken_over():
    assert data_view.match("Show cattle prices from January to June 2026") is None
    assert data_view.match("how many kilos in June 2026?") is None
    assert data_view.match("show the data for 2025") == "show_data_raw"   # a date range is now allowed
    assert data_view.match("thank you") is None
    assert data_view.match("ok") is None


def test_monthly_table(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "A", THREE)
    text, widget = data_view.reply(ds, "show_data", "en")
    assert "2 months" in text and "3 records" in text
    assert widget["widget"] == "table" and widget["kind"] == "monthly"
    assert widget["rows"][0] == ["January 2026", 2000.0, 20, 100.0, 2]
    assert len(widget["columns"]) == len(widget["rows"][0]) == 5
    assert widget["export_url"].endswith("kind=monthly")


def test_filipino_table_uses_filipino_months(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "A", THREE)
    text, widget = data_view.reply(ds, "show_data", "fil")
    assert widget["rows"][0][0] == "Enero 2026"
    assert widget["columns"][0]["label"] == "Buwan"
    assert widget["title"] == "Buwanang buod"


def test_raw_table_is_limited_and_newest_first(tmp_path, monkeypatch):
    dates = pd.date_range("2025-01-01", periods=250).strftime("%Y-%m-%d").tolist()
    ds = make_dataset(tmp_path, monkeypatch, "A", dates)
    text, widget = data_view.reply(ds, "show_data_raw", "en")
    assert widget["total_rows"] == 250
    assert len(widget["rows"]) == 200
    assert widget["rows"][0][0] == dates[-1]
    assert widget["rows"][0][0] > widget["rows"][-1][0]
    assert "latest 200 of 250" in text


def test_tables_stay_per_dataset(tmp_path, monkeypatch):
    a = make_dataset(tmp_path, monkeypatch, "A", THREE, price=100.0)
    b = make_dataset(tmp_path, monkeypatch, "B", THREE, price=250.0)
    assert data_view.reply(a, "show_data", "en")[1]["rows"][0][3] == 100.0
    assert data_view.reply(b, "show_data", "en")[1]["rows"][0][3] == 250.0


def test_empty_dataset_gets_the_normal_message(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "Empty", [])
    text, widget = data_view.reply(ds, "show_data", "en")
    assert text == rb.t("en", "empty_dataset") and widget is None


def test_chat_engine_returns_and_saves_the_table(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "A", THREE)
    result = chat_engine.answer(ds, "Show the data")
    assert result["intent"] == "show_data" and result["confidence"] == 1.0
    assert result["chart"]["widget"] == "table"
    saved = db.get_chat_history(ds)[-1]["chart"]          # a reload restores the table
    assert saved["widget"] == "table" and saved["rows"][0][0] == "January 2026"
    raw = chat_engine.answer(ds, "show raw records")
    assert raw["intent"] == "show_data_raw" and len(raw["chart"]["rows"]) == 3


def test_csv_export(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "A", THREE)
    monthly = data_view.export_csv(ds, "monthly").splitlines()
    assert monthly[0] == "month,total_kilos,head_count,price_per_kilo_weighted,records"
    assert len(monthly) == 3
    raw = data_view.export_csv(ds, "raw").splitlines()
    assert raw[0] == "date,head_count,total_kilos,price_per_kilo" and len(raw) == 4


def test_export_route(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "A", THREE)
    client = flask_app.test_client()
    ok = client.get("/api/datasets/%d/export.csv?kind=raw" % ds)
    assert ok.status_code == 200 and ok.content_type.startswith("text/csv")
    assert "attachment" in ok.headers["Content-Disposition"]
    assert client.get("/api/datasets/99999/export.csv").status_code == 404
    assert client.get("/api/datasets/%d/export.csv?kind=nope" % ds).status_code == 400
