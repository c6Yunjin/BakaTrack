import pytest

from modules import query_engine as qe


def rec(date, heads, kilos, price):
    return {"date": date, "head_count": heads, "total_kilos": kilos, "price_per_kilo": price}


RECORDS = [
    rec("2026-01-05", 10, 1000, 200),
    rec("2026-01-20", 20, 3000, 220),
    rec("2026-02-10", 5, 500, 100),
    rec("2026-03-10", 8, 800, 300),
]


def test_monthly_totals_match_manual():
    # TC-09: January = 1000+3000 kilos, 10+20 heads, price (200*1000+220*3000)/4000
    months = qe.summarize_records(RECORDS)
    jan = months[0]
    assert jan["total_kilos"] == 4000
    assert jan["head_count"] == 30
    assert jan["price_per_kilo"] == pytest.approx(215.0)
    assert len(months) == 3


def test_totals_peak_lowest():
    summary = {"months": qe.summarize_records(RECORDS)}
    assert qe.total_of(summary, "total_kilos") == 5300
    assert qe.peak_month(summary, "price_per_kilo")["key"] == "2026-03"
    assert qe.lowest_month(summary, "price_per_kilo")["key"] == "2026-02"


def test_gaps_are_reported_not_filled():
    months = qe.summarize_records([rec("2026-01-05", 1, 100, 10), rec("2026-03-05", 1, 100, 10)])
    assert len(months) == 2
    assert qe.find_gaps(months) == ["2026-02"]


def test_compare_months():
    summary = {"months": qe.summarize_records(RECORDS)}
    result = qe.compare_months(summary, (2026, 1), (2026, 3))
    assert result["found"] is True
    assert result["difference"] == pytest.approx(85.0)
    missing = qe.compare_months(summary, (2026, 1), (2026, 7))
    assert missing["found"] is False


def test_empty_range_has_no_data(monkeypatch):
    # TC-13: no records means "no data", never invented numbers
    monkeypatch.setattr(qe.db, "get_records", lambda *a, **k: [])
    summary = qe.get_summary(1, "2030-01-01", "2030-06-30")
    assert summary["has_data"] is False
    assert summary["months_used"] == 0
