"""Chat engine (Step 6): follows the project flow chart for ONE question.

preprocess -> intent (ANN) -> 60% rule -> date parser -> no-data check
-> query -> response builder -> save to chat logs.
The dataset_id is passed in every time, so tabs never mix.
"""
import time
import traceback

from database import db
from modules import query_engine, response_builder as rb
from nlp.date_parser import parse_query
from nlp.intent_classifier import predict
from nlp.language import detect_language

STATIC_INTENTS = {"greeting", "goodbye", "help", "upload_help", "out_of_scope"}
NOT_READY_INTENTS = {"show_chart", "forecast", "price_rating"}   # built in later steps


def _reply_for(dataset_id, message, lang, intent, confidence, is_confident):
    if not message.strip():
        return rb.t(lang, "empty_message")
    if not is_confident:                                   # 60% rule: referral message
        return rb.t(lang, "referral", conf=round(confidence * 100))
    if intent in STATIC_INTENTS:
        return rb.t(lang, intent)
    if intent in NOT_READY_INTENTS:
        return rb.t(lang, "coming")

    latest = db.get_latest_date(dataset_id)
    if latest is None:
        return rb.t(lang, "empty_dataset")
    parsed = parse_query(message, latest)
    summary = query_engine.get_summary(dataset_id, parsed["start"], parsed["end"])
    if not summary["has_data"]:                            # no-data message, no invented numbers
        return rb.t(lang, "no_data", start=parsed["start"], end=parsed["end"])
    return rb.build_answer(intent, lang, parsed, summary)


def answer(dataset_id, message):
    """Answer one question for one dataset. Returns a dict for the web page."""
    started = time.time()
    lang = detect_language(message)
    intent, confidence, is_confident = None, 0.0, False
    try:
        if message.strip():
            intent, confidence, is_confident = predict(message)
        reply = _reply_for(dataset_id, message, lang, intent, confidence, is_confident)
    except Exception:
        traceback.print_exc()                              # show the real error in the terminal
        reply = rb.t(lang, "error")
    try:
        db.save_chat_log(dataset_id, message, intent, confidence, reply)
    except Exception:
        traceback.print_exc()
    return {"reply": reply, "intent": intent, "confidence": round(float(confidence), 3),
            "language": lang, "seconds": round(time.time() - started, 3)}
