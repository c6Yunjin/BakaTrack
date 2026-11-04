import pandas as pd

from database import db
from modules import chat_engine, easter_eggs as eg


def make_dataset(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-15"], "head_count": [10],
                       "total_kilos": [1000.0], "price_per_kilo": [100.0]})
    return db.create_dataset_with_records("T", "test", df)


def test_stretched_greeting_matches_and_echoes_the_time():
    assert eg.match("gooood morning everyone!") == "egg_greeting"
    assert eg.match("GOOOOOOD EVENING po maam") == "egg_greeting"
    assert eg.match("goood day class!") == "egg_greeting"
    text, widget = eg.reply("egg_greeting", "goooood afternoon", "en")
    assert text.startswith("Good afternoon, Maam Marianne!") and widget is None


def test_plain_greeting_and_real_questions_are_not_taken():
    assert eg.match("good morning") is None
    assert eg.match("good evening") is None
    assert eg.match("gooood morning how many kilos in june 2026") is None
    assert eg.match("how many kilos in June 2026?") is None
    assert eg.match("show the data") is None
    assert eg.match("ok") is None


def test_rickroll_and_cow_triggers():
    for phrase in ("rickroll", "Rick Roll", "play rickroll.mp4", "Never gonna give you up"):
        assert eg.match(phrase) == "egg_rickroll"
    for phrase in ("cow animation", "play animation", "cow party"):
        assert eg.match(phrase) == "egg_cows"


def test_comply_quote():
    for phrase in ("I can't comply", "i cant comply po", "cannot comply"):
        assert eg.match(phrase) == "egg_comply"
    assert eg.reply("egg_comply", "i cant comply", "en")[0] == "Daaaahil?"


def test_other_eggs_match():
    assert eg.match("tell me a joke") == "egg_joke"
    assert eg.match("who made you?") == "egg_who_made_you"
    assert eg.match("1.0 po") == "egg_grade"
    assert eg.match("meaning of life") == "egg_life"
    assert eg.match("sing") == "egg_sing"


def test_replies_and_widgets():
    assert eg.reply("egg_joke", "tell me a joke", "en")[0] in eg.JOKES["en"]
    assert eg.reply("egg_joke", "joke", "fil")[0] in eg.JOKES["fil"]
    assert eg.reply("egg_rickroll", "rickroll", "en")[1] == {"widget": "egg", "kind": "rickroll"}
    assert eg.reply("egg_cows", "cows", "en")[1] == {"widget": "egg", "kind": "cows"}
    for intent in eg.INTENTS - {"egg_greeting", "egg_joke"}:
        for lang in ("en", "fil", "taglish"):
            assert eg.reply(intent, "x", lang)[0]


def test_chat_engine_runs_eggs_and_saves_the_widget(tmp_path, monkeypatch):
    ds = make_dataset(tmp_path, monkeypatch)
    greeting = chat_engine.answer(ds, "goooood morning everyone!")
    assert greeting["intent"] == "egg_greeting" and "Maam Marianne" in greeting["reply"]
    assert chat_engine.answer(ds, "I can't comply")["reply"] == "Daaaahil?"
    roll = chat_engine.answer(ds, "rickroll")
    assert roll["chart"] == {"widget": "egg", "kind": "rickroll"}
    assert db.get_chat_history(ds)[-1]["chart"] == {"widget": "egg", "kind": "rickroll"}


def test_switch_off(monkeypatch):
    monkeypatch.setattr(eg, "ENABLED", False)
    assert eg.match("rickroll") is None and eg.match("gooood morning") is None
