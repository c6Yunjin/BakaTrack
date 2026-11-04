import pandas as pd

from database import db
from modules import chat_engine, smalltalk


def test_short_phrases_match():
    assert smalltalk.match("Thank you!")[0] == "smalltalk_thanks"
    assert smalltalk.match("salamat po") == ("smalltalk_thanks", "fil")
    assert smalltalk.match("who are you?")[0] == "smalltalk_who_are_you"
    assert smalltalk.match("How are you")[0] == "smalltalk_how_are_you"
    assert smalltalk.match("ok")[0] == "smalltalk_ack"


def test_greeting_then_ask_matches():
    assert smalltalk.match("good evening po, magtatanong lang ako") == ("smalltalk_ask", "fil")


def test_real_questions_are_never_taken_over():
    assert smalltalk.match("ok thanks see you") == (None, None)            # goodbye stays with the ANN
    assert smalltalk.match("thank you for the kilos in June 2026") == (None, None)
    assert smalltalk.match("how many kilos in June 2026?") == (None, None)
    assert smalltalk.match("kumusta ang presyo ngayon") == (None, None)


def test_every_rule_has_three_languages():
    for intent in smalltalk.INTENTS:
        for lang in ("en", "fil", "taglish"):
            assert smalltalk.reply(intent, lang)


def test_chat_engine_uses_the_rule(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    db.init_db()
    df = pd.DataFrame({"date": ["2026-01-15"], "head_count": [10],
                       "total_kilos": [1000.0], "price_per_kilo": [100.0]})
    ds = db.create_dataset_with_records("T", "test", df)
    result = chat_engine.answer(ds, "thank you")
    assert result["intent"] == "smalltalk_thanks"
    assert result["reply"].startswith("You're welcome")
    assert chat_engine.answer(ds, "salamat po")["language"] == "fil"
