import pandas as pd
import pytest

from database import db
from modules import chart_maker, chat_engine
from modules import query_engine as qe


def rec(date, price):
    return {"date": date, "head_count": 10, "total_kilos": 100, "price_per_kilo": price}


def summary_of(records):
    return {"months": qe.summarize_records(records)}


def test_chart_values_match_data():
    # TC-10: 6 months of records -> 6 points with the correct values
    records = [rec("2026-%02d-15" % m, 100 + 10 * (m - 1)) for m in range(1, 7)]
    chart = chart_maker.build_chart(summary_of(records), "price_per_kilo", "line", "en")
    assert chart["values"] == [100, 110, 120, 130, 140, 150]
    assert chart["labels"][0] == "Jan 2026" and chart["labels"][-1] == "Jun 2026"


def test_missing_month_is_a_gap_not_a_number():
    chart = chart_maker.build_chart(
        summary_of([rec("2026-01-15", 100), rec("2026-03-15", 120)]), "price_per_kilo", "line", "en")
    assert chart["values"] == [100, None, 120]


def test_chart_type_choice():
    assert chart_maker.chart_type_for("price_per_kilo", "show prices") == "line"
    assert chart_maker.chart_type_for("total_kilos", "show kilos") == "bar"
    assert chart_maker.chart_type_for("total_kilos", "show kilos as line") == "line"


def test_show_chart_question_returns_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-%02d-15" % m for m in range(1, 7)],
                       "head_count": [10] * 6, "total_kilos": [100.0] * 6,
                       "price_per_kilo": [100.0 + 10 * i for i in range(6)]})
    ds = db.create_dataset_with_records("T", "test", df)
    r = chat_engine.answer(ds, "Show cattle prices from January to June 2026")
    assert r["intent"] == "show_chart"
    assert r["chart"] is not None and len(r["chart"]["values"]) == 6
    assert "Highest" in r["reply"] and "Lowest" in r["reply"]
