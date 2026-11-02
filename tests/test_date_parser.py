# Step 4 tests: TC-02 to TC-05 plus extra cases. "Latest record" is set to 2026-10-31.
from nlp.date_parser import parse_query

LATEST = "2026-10-31"


def p(text):
    return parse_query(text, LATEST)


def test_tc02_filipino_months():
    r = p("mula Enero hanggang Hunyo 2026")
    assert (r["start"], r["end"]) == ("2026-01-01", "2026-06-30")


def test_tc03_english_dates():
    r = p("from March 1 to August 31, 2026")
    assert (r["start"], r["end"]) == ("2026-03-01", "2026-08-31")


def test_tc04_reversed_dates():
    r = p("Hunyo hanggang Enero")
    assert r["swapped"] is True
    assert (r["start"], r["end"]) == ("2026-01-01", "2026-06-30")
    assert any("swapped" in n for n in r["notes"])


def test_tc05_metrics():
    assert p("ilang kilo ang na-trade")["metric"] == "total_kilos"
    assert p("magkano ang total weight noong mayo")["metric"] == "total_kilos"
    assert p("ilang baka ang nabenta")["metric"] == "head_count"
    assert p("ilang ulo noong marso")["metric"] == "head_count"
    assert p("magkano ang presyo")["metric"] == "price_per_kilo"
    assert p("presyo ng baka")["metric"] == "price_per_kilo"
    assert p("ilang kilo ng baka")["metric"] == "total_kilos"


def test_tc08_show_prices_range():
    r = p("Show cattle prices from January to June 2026")
    assert (r["start"], r["end"]) == ("2026-01-01", "2026-06-30")
    assert r["metric"] == "price_per_kilo"


def test_slash_and_iso_dates():
    assert p("03/01/2026")["start"] == "2026-03-01"
    r = p("from 2026-03-01 to 2026-06-30")
    assert (r["start"], r["end"]) == ("2026-03-01", "2026-06-30")


def test_last_n_months():
    r = p("kilos traded last 6 months")
    assert (r["start"], r["end"]) == ("2026-05-01", "2026-10-31")
    r = p("nitong nakaraang 3 buwan")
    assert r["start"] == "2026-08-01"


def test_this_and_last_year():
    r = p("total kilo ngayong taon")
    assert (r["start"], r["end"]) == ("2026-01-01", "2026-12-31")
    r = p("total kilos last year")
    assert (r["start"], r["end"]) == ("2025-01-01", "2025-12-31")


def test_last_month():
    r = p("head count noong nakaraang buwan")
    assert (r["start"], r["end"]) == ("2026-09-01", "2026-09-30")


def test_single_month_and_given_year():
    r = p("total kilos noong Hunyo")
    assert (r["start"], r["end"]) == ("2026-06-01", "2026-06-30")
    r = p("Enero hanggang Hunyo 2025")
    assert (r["start"], r["end"]) == ("2025-01-01", "2025-06-30")


def test_defaults_are_stated():
    r = p("Anong buwan pinakamataas ang presyo?")
    assert r["range_found"] is False
    assert (r["start"], r["end"]) == ("2026-05-01", "2026-10-31")
    assert any("latest 6 months" in n for n in r["notes"])
    r = p("show chart from january to june 2026")
    assert r["metric_found"] is False and r["metric"] == "price_per_kilo"


def test_may_is_not_always_a_month():
    assert p("May tanong ako")["range_found"] is False
    assert p("from March to May")["end"] == "2026-05-31"


def test_compare_months():
    r = p("mas mataas ba ang presyo noong marso kaysa abril")
    assert r["months"] == [(2026, 3), (2026, 4)]
    assert (r["start"], r["end"]) == ("2026-03-01", "2026-04-30")


def test_next_month_flag():
    assert p("forecast for next month")["wants_next_month"] is True
