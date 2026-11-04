# Raw records for a date range: "show the data for November 2025".
import csv
import io

import pandas as pd

from database import db
from modules import chat_engine, data_view as dv


def make_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2025-10-20", "2025-11-03", "2025-11-17", "2025-12-01"],
                       "head_count": [10, 20, 30, 40],
                       "total_kilos": [1000.0, 2000.0, 3000.0, 4000.0],
                       "price_per_kilo": [100.0, 110.0, 120.0, 130.0]})
    return db.create_dataset_with_records("T", "test", df)


def test_range_requests_are_matched():
    for phrase in ("show the data for November 2025", "show me november data",
                   "ipakita ang data noong Nobyembre",
                   "show records from October to December 2025",
                   "give me the records for last 2 months"):
        assert dv.match(phrase) == "show_data_raw", phrase


def test_other_questions_are_not_taken():
    for phrase in ("how many kilos were traded in november", "show the price data for november",
                   "show chart for november", "Compare prices of March and June 2026"):
        assert dv.match(phrase) is None, phrase
    assert dv.match("show the data") == "show_data"
    assert dv.match("show raw data") == "show_data_raw"


def test_only_november_rows(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text, widget = dv.reply(ds, "show_data_raw", "en", "show the data for November 2025")
    assert widget["total_rows"] == 2
    assert [r[0] for r in widget["rows"]] == ["2025-11-17", "2025-11-03"]
    assert "November 1, 2025" in text and "start=2025-11-01" in widget["export_url"]


def test_range_without_records(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text, widget = dv.reply(ds, "show_data_raw", "en", "show the data for February 2025")
    assert widget is None and "no records" in text.lower()


def test_plain_show_data_is_unchanged(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    assert dv.reply(ds, "show_data_raw", "en", "show raw data")[1]["total_rows"] == 4
    assert dv.reply(ds, "show_data_raw", "en")[1]["total_rows"] == 4


def test_chat_engine_uses_the_range(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    out = chat_engine.answer(ds, "ipakita ang data noong Nobyembre 2025")
    assert out["intent"] == "show_data_raw" and out["chart"]["total_rows"] == 2


def test_csv_export_range(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    rows = list(csv.reader(io.StringIO(dv.export_csv(ds, "raw", "2025-11-01", "2025-11-30"))))
    assert len(rows) == 3 and rows[0][0] == "date"          # header + 2 November rows


def test_download_route_passes_the_dates(tmp_path, monkeypatch):
    from app import app
    ds = make_dataset(tmp_path, monkeypatch)
    resp = app.test_client().get("/api/datasets/%d/export.csv?kind=raw&start=2025-11-01&end=2025-11-30" % ds)
    assert resp.status_code == 200
    assert len(resp.get_data(as_text=True).strip().splitlines()) == 3
