# Knowledge base: Padre Garcia facts with sources, and real questions are never taken over.
import pandas as pd

from database import db
from modules import chat_engine, knowledge_base as kb


def make_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-15", "2026-02-15"], "head_count": [10, 12],
                       "total_kilos": [1000.0, 1200.0], "price_per_kilo": [100.0, 110.0]})
    return db.create_dataset_with_records("T", "test", df)


def test_questions_are_matched():
    cases = {
        "saan ang baka capital": "kb_capital",
        "what is the cattle capital of the philippines": "kb_capital",
        "kailan nagsimula ang bakahan": "kb_history",
        "when did the cattle market start": "kb_history",
        "kailan ang bakahan": "kb_trading_day",
        "what day is the cattle auction": "kb_trading_day",
        "when is the kabakahan festival": "kb_festival",
        "where is the cattle market": "kb_where",
        "saan ang bakahan": "kb_where",
    }
    for text, expected in cases.items():
        assert kb.match(text) == expected, text


def test_real_questions_are_not_taken():
    for text in ("how many cattle were sold in padre garcia", "total kilos in november",
                 "ano ang panahon bukas", "where is this data from", "show data for batangas",
                 "Compare prices of March and June 2026", "what is the price of baka"):
        assert kb.match(text) is None, text


def test_every_entry_has_three_languages_and_a_source():
    for entry in kb.ENTRIES:
        assert entry["source"]
        for lang in ("en", "fil", "taglish"):
            assert entry["answers"][lang]
            text = kb.reply("kb_" + entry["id"], lang)
            assert entry["source"] in text


def test_chat_engine_answers_from_the_knowledge_base(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    out = chat_engine.answer(ds, "saan ang baka capital")
    assert out["intent"] == "kb_capital"
    assert "Cattle Trading Capital of the Philippines" in out["reply"]
    assert "Source" in out["reply"] or "Pinagmulan" in out["reply"]
    out = chat_engine.answer(ds, "Compare prices of January and February 2026")
    assert not str(out["intent"]).startswith("kb_")
