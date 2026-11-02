import pandas as pd

from database import db
from modules import fuzzy_rater as fr


def test_high_price_is_rated_high():
    # TC-06: price 20% above average
    assert fr.infer(1.2)["label"] == "high"


def test_normal_price_is_rated_normal():
    # TC-07: price equal to the average
    result = fr.infer(1.0)
    assert result["label"] == "normal"
    assert abs(result["score"] - 50) < 1


def test_low_price_is_rated_low():
    assert fr.infer(0.8)["label"] == "low"


def test_overlap_gives_two_memberships():
    m = fr.infer(1.1)["memberships"]
    assert m["normal"] > 0 and m["high"] > 0 and m["low"] == 0


def test_huge_ratio_is_clamped():
    assert fr.infer(5)["label"] == "high"


def make_dataset(tmp_path, monkeypatch, prices):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-%02d-15" % (i + 1) for i in range(len(prices))],
                       "head_count": [10] * len(prices), "total_kilos": [1000.0] * len(prices),
                       "price_per_kilo": prices})
    return db.create_dataset_with_records("T", "test", df)


def test_rate_answer_high(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, [100.0, 100.0, 100.0, 160.0])
    text = fr.rate_answer(ds, "en", {"months": []})
    assert "High" in text and "above" in text and "Guide only" in text
    assert "Mataas" in fr.rate_answer(ds, "fil", {"months": []})


def test_rate_needs_enough_months(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch, [100.0, 120.0])
    assert "at least 3 months" in fr.rate_answer(ds, "en", {"months": []})
