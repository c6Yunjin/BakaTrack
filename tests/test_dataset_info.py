# Dataset info: "what dates do you have?", empty ranges, and highest month over all the data.
import pandas as pd

from database import db
from modules import chat_engine, dataset_info as di


def make_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    prices = [100, 105, 140, 110, 108, 107, 106, 104, 103, 102, 101, 100]     # highest in March
    df = pd.DataFrame({"date": ["2025-%02d-15" % m for m in range(1, 13)],
                       "head_count": [10] * 12, "total_kilos": [1000.0] * 12, "price_per_kilo": prices})
    return db.create_dataset_with_records("T", "test", df)


def test_questions_are_matched():
    for phrase in ("what dates do you have?", "What is the date range?", "when does the data start",
                   "how much data do you have", "saan nagsisimula ang data", "anong petsa ang meron ka po"):
        assert di.match(phrase) == "dataset_info", phrase


def test_real_questions_are_not_taken():
    for phrase in ("show the data", "show the data for November", "how many kilos in June",
                   "date range for november 2025", "total kilos last 6 months", "show chart this year"):
        assert di.match(phrase) is None, phrase


def test_reply_states_this_datasets_dates(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    text = di.reply(ds, "en")
    assert "12 records" in text and "January 15, 2025" in text and "December 15, 2025" in text
    assert "12 months" in text


def test_chat_engine_answers_dates_in_both_languages(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    out = chat_engine.answer(ds, "what dates do you have?")
    assert out["intent"] == "dataset_info" and "12 records" in out["reply"]
    out = chat_engine.answer(ds, "saan nagsisimula ang data")
    assert out["intent"] == "dataset_info" and "12" in out["reply"]


def test_empty_range_says_where_the_data_runs(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    reply = chat_engine.answer(ds, "total kilos in June 2019")["reply"]
    assert "no records" in reply.lower() and "January 15, 2025" in reply


def test_highest_month_uses_all_the_data(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    reply = chat_engine.answer(ds, "Which month has the highest price?")["reply"]
    assert "March 2025" in reply and "all 12 months" in reply
    assert "latest 6 months" not in reply


def test_given_dates_still_win(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    reply = chat_engine.answer(ds, "Which month has the highest price from July to December 2025?")["reply"]
    assert "all 12 months" not in reply and "July 2025" in reply
