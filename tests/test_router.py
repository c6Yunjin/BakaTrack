import pytest

from database import db
from modules import chat_engine
from modules import semantic_router as sr

CASES = [
    ("can you please tell me what is the most recent price per kilo of cattle in the dataset", "latest_price"),
    ("kumusta po, gusto ko lang malaman kung ano ang pinakabagong presyo ng baka kasi bibili ako bukas", "latest_price"),
    ("hi, i am a buyer from lipa and i was wondering if you could tell me, based on the data you have, what was the latest price of cattle per kilo", "latest_price"),
    ("hello po, pwede ko bang malaman kung ano ang kabuuang halaga ng lahat ng baka na nabenta nitong nakaraang buwan", "total_value"),
    ("how heavy is one cow on average", "weight_per_head"),
    ("give me an overview of the baka market", "market_summary"),
    ("which place is this data about", "location_info"),
    ("good afternoon, can you tell me which place this data is from and also if it is real or sample data", "location_info"),
    ("how many records are in this dataset and what is the date range", "dataset_info"),
    ("what can you do", "sys_about"),
    ("how do you work", "sys_how"),
    ("what is your accuracy", "sys_accuracy"),
    ("are you using chatgpt", "sys_ai"),
    ("what languages do you understand", "sys_languages"),
    ("how does the forecast work", "sys_forecast_how"),
    ("how does the fuzzy rating work", "sys_rating_how"),
    ("what are your limits", "sys_limits"),
]
NEVER = [
    "Compare prices of March and June 2026", "price of baka", "Ano ang panahon bukas?",
    "what is the weather in manila", "who is the president of the philippines", "hello",
    "forecast next month", "total kilos in June 2026", "show chart of prices",
    "how many cattle from march to may 2026", "what is the price rating in october 2026",
    "capital of france", "where can i upload my data",
]


@pytest.mark.parametrize("text,expected", CASES)
def test_reworded_and_long_questions(text, expected):
    assert sr.match(text) == expected


@pytest.mark.parametrize("text", NEVER)
def test_real_questions_are_not_taken_over(text):
    assert sr.match(text) is None


def test_chat_answers_system_questions(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "t.db"))
    db.init_db()
    r = chat_engine.answer(1, "what is your accuracy")
    assert r["intent"] == "sys_accuracy" and "84.76%" in r["reply"]
    r = chat_engine.answer(1, "paano ka gumagana")
    assert r["intent"] == "sys_how" and "offline" in r["reply"]


def test_near_miss_format(monkeypatch):
    class Fake:
        entries = {"sys_about": {"title": {"en": "What can you do?"}}}

        def decide(self, message):
            return "near", "sys_about", 0.4

    monkeypatch.setattr(sr, "_get", lambda: Fake())
    assert sr.near_miss("who are you", "en").startswith("I am not sure")
    assert "What can you do?" in sr.near_miss("who are you", "en")


FIXED = [
    ("what's the current going rate for cattle per kilo", "latest_price"),
    ("how big is the dataset", "dataset_info"),
    ("what period of time does your data go back to", "dataset_info"),
    ("is the data you have from a real market or just made up", "sys_limits"),
    ("good afternoon, can you tell me which place this data is from and also if it is real or sample data", "location_info"),
]
STILL_NEVER = ["how is the forecast for next month", "what is the price rating", "how is the price rating now"]


@pytest.mark.parametrize("text,expected", FIXED)
def test_fixed_wordings(text, expected):
    assert sr.match(text) == expected


@pytest.mark.parametrize("text", STILL_NEVER)
def test_still_not_taken_over(text):
    assert sr.match(text) is None
