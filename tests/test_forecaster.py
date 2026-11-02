import pandas as pd

from database import db
from modules import forecaster as fc


def make_dataset(tmp_path, monkeypatch, name, prices):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-%02d-15" % (i + 1) for i in range(len(prices))],
                       "head_count": [10] * len(prices), "total_kilos": [1000.0] * len(prices),
                       "price_per_kilo": prices})
    return db.create_dataset_with_records(name, "test", df)


def test_straight_line_forecast_is_exact(tmp_path, monkeypatch):
    # prices 100, 110, ... 170 -> the next month must be 180
    ds = make_dataset(tmp_path, monkeypatch, "T", [100.0 + 10 * i for i in range(8)])
    text = fc.forecast_answer(ds, "en")
    assert "\u20b1180.00" in text
    assert "September 2026" in text
    assert "guide only" in text


def test_forecast_refused_when_history_is_short(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, "T", [100.0, 110.0, 120.0, 130.0])
    assert "at least 6 months" in fc.forecast_answer(ds, "en")


def test_two_datasets_forecast_differently(tmp_path, monkeypatch):
    # TC-11: each dataset forecasts from its own months only
    a = make_dataset(tmp_path, monkeypatch, "A", [100.0] * 8)
    b = make_dataset(tmp_path, monkeypatch, "B", [200.0] * 8)
    assert "\u20b1100.00" in fc.forecast_answer(a, "en")
    assert "\u20b1200.00" in fc.forecast_answer(b, "en")


def test_next_month_rolls_over_the_year():
    assert fc.next_month(2026, 12) == (2027, 1)
    assert fc.next_month(2026, 3) == (2026, 4)
