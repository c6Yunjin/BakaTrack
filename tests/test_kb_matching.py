import pytest

from database import db
from modules import chat_engine
from modules import knowledge_base as kb

REWORDED = [
    ("what or where is the cattle trading capital in the ph", "kb_capital"),
    ("capital of cattle trading in the philippines", "kb_capital"),
    ("saan po ang cattle trading capital sa pinas", "kb_capital"),
    ("capitl of cattle tradng", "kb_capital"),
    ("when did the bakahan begin", "kb_history"),
    ("kailan po nagsimula ang bakahan sa padre garcia", "kb_history"),
    ("kailan ang kabakahan festival", "kb_festival"),
    ("what day is the cattle market open", "kb_trading_day"),
    ("open ba ang bakahan sa friday", "kb_trading_day"),
    ("where is the bakahan located", "kb_where"),
    ("nasaan ang padre garcia", "kb_where"),
]
NEVER_TAKEN = [
    "Compare prices of March and June 2026", "price of baka", "Ano ang panahon bukas?",
    "who is the president of the philippines", "capital of france", "hello",
    "show data for batangas", "where is this data from", "magkano ang baka ngayon",
    "forecast next month", "what is the weather in manila",
]


@pytest.mark.parametrize("text,expected", REWORDED)
def test_reworded_questions_match(text, expected):
    assert kb.match(text) == expected


@pytest.mark.parametrize("text", NEVER_TAKEN)
def test_real_questions_are_not_taken_over(text):
    assert kb.match(text) is None


def test_chat_answers_the_long_capital_question(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    db.init_db()
    r = chat_engine.answer(1, "what or where is the cattle trading capital in the ph")
    assert r["intent"] == "kb_capital"
    assert "General fact" in r["reply"] and "Source:" in r["reply"]


def test_near_miss_format(monkeypatch):
    class Fake:
        titles = {"capital": {"en": "Where is the cattle trading capital of the Philippines?"}}

        def decide(self, message):
            return "near", "capital", 0.3

    monkeypatch.setattr(kb, "_get_matcher", lambda: Fake())
    text = kb.near_miss("padre garcia cattle", "en")
    assert text.startswith("I am not sure") and "cattle trading capital" in text
    assert kb.near_miss("show me the price chart", "en") is None   # blocked words: never a near miss
