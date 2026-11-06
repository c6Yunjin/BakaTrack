import pandas as pd

from database import db
from modules import chat_engine, location_rules as lr


def make_dataset(tmp_path, monkeypatch, name="Lipa tab", location="Lipa City"):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-10", "2026-02-15"], "head_count": [10, 20],
                       "total_kilos": [1000.0, 2000.0], "price_per_kilo": [100.0, 210.0]})
    ds = db.create_dataset_with_records(name, "test", df)
    if location:
        db.set_dataset_location(ds, location)
    return ds


def test_matching():
    for question in ["Show data for batangas", "show data for Lipa", "Show data for Padre Garcia",
                     "ipakita ang data ng Tanauan", "show data for Cebu", "Lipa data"]:
        assert lr.match(question) == "location_data", question
    for question in ["where is this data from", "saan galing ang datos", "what location is this dataset",
                     "where does the data come from"]:
        assert lr.match(question) == "location_info", question


def test_real_questions_are_never_taken_over():
    for question in ["show the data", "Show data for January 2026", "show data for the last 6 months",
                     "show data for this month", "total kilos in June 2026", "total kilos in Lipa",
                     "what dates do you have", "Show cattle prices from January to June 2026",
                     "where is the cattle market", "price of baka", "hello"]:
        assert lr.match(question) is None, question


def test_own_place_shows_the_table(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text, widget = lr.reply(ds, "show data for Lipa", "location_data", "en")
    assert text.startswith("This dataset is from Lipa City, Batangas, so here is its data.")
    assert widget["widget"] == "table"


def test_other_place_is_refused_and_points_to_the_right_tab(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text, widget = lr.reply(ds, "show data for Tanauan", "location_data", "en")
    assert widget is None
    assert "from Lipa City, Batangas" in text and "no records for Tanauan City" in text
    assert "No dataset in this app is from Tanauan City" in text
    make_dataset(tmp_path, monkeypatch, name="Tanauan tab", location="Tanauan City")
    text, _ = lr.reply(ds, "show data for Tanauan", "location_data", "en")
    assert 'The dataset "Tanauan tab" is from Tanauan City' in text
    fil, _ = lr.reply(ds, "show data for Tanauan", "location_data", "fil")
    assert "Wala akong talaan para sa Tanauan City" in fil


def test_province_and_outside_places(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text, widget = lr.reply(ds, "Show data for batangas", "location_data", "en")
    assert "covers Lipa City, Batangas only" in text and widget["widget"] == "table"
    text, widget = lr.reply(ds, "show data for Cebu", "location_data", "en")
    assert text.startswith("I only cover places in Batangas.") and "Lipa City, Batangas" in text
    assert widget is None


def test_location_info_and_unset_location(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    assert lr.reply(ds, "where is this data from", "location_info", "en")[0] == "This dataset is from Lipa City, Batangas."
    sample = make_dataset(tmp_path, monkeypatch, name="PGPC (SAMPLE)", location="Padre Garcia")
    text, _ = lr.reply(sample, "where is this data from", "location_info", "en")
    assert "Padre Garcia, Batangas" in text and "fake" in text
    nowhere = make_dataset(tmp_path, monkeypatch, name="No place", location=None)
    assert "no location set" in lr.reply(nowhere, "where is this data from", "location_info", "en")[0]
    assert "do not know which place" in lr.reply(nowhere, "show data for Lipa", "location_data", "en")[0]


def test_scope_block_stops_wrong_place_questions(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    assert "no records for Tanauan City" in lr.scope_block(ds, "total kilos in Tanauan", "total_kilos", "en")
    assert lr.scope_block(ds, "total kilos in Lipa this month", "total_kilos", "en") is None
    assert lr.scope_block(ds, "total kilos in Batangas", "total_kilos", "en") is None
    assert lr.scope_block(ds, "hello from Tanauan", "greeting", "en") is None
    assert lr.scope_block(ds, "total kilos in June 2026", "total_kilos", "en") is None


def test_chat_engine_uses_the_location_rules(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    out = chat_engine.answer(ds, "show data for Lipa")
    assert out["intent"] == "location_data" and out["chart"]["widget"] == "table"
    out = chat_engine.answer(ds, "Show data for Tanauan")
    assert out["intent"] == "location_data" and "no records for Tanauan City" in out["reply"]
    out = chat_engine.answer(ds, "where is this data from")
    assert out["reply"] == "This dataset is from Lipa City, Batangas."
