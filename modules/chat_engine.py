"""Chat engine: follows the project flow chart for ONE question.

preprocess -> intent (ANN) -> 60% rule -> date parser -> no-data check
-> query -> response builder (+ chart) -> save to chat logs.
The dataset_id is passed in every time, so tabs never mix.
"""
import time
import traceback

from database import db
from modules import chart_maker, forecaster, fuzzy_rater, query_engine, response_builder as rb
from nlp.date_parser import parse_query
from nlp.intent_classifier import predict
from nlp.language import detect_language

STATIC_INTENTS = {"greeting", "goodbye", "help", "upload_help", "out_of_scope"}
NOT_READY_INTENTS = set()      # built in later steps


def _reply_for(dataset_id, message, lang, intent, confidence, is_confident):
    """Returns (text, chart). chart is None when there is nothing to draw."""
    if not message.strip():
        return rb.t(lang, "empty_message"), None
    if not is_confident:                               # 60% rule: referral message
        return rb.t(lang, "referral", conf=round(confidence * 100)), None
    if intent in STATIC_INTENTS:
        return rb.t(lang, intent), None
    if intent in NOT_READY_INTENTS:
        return rb.t(lang, "coming"), None

    latest = db.get_latest_date(dataset_id)
    if latest is None:
        return rb.t(lang, "empty_dataset"), None
    parsed = parse_query(message, latest)
    if intent == "price_rating":              # rates against the whole dataset history
        return fuzzy_rater.rate_answer(dataset_id, lang, parsed), None
    if intent == "forecast":                  # forecasts from this dataset's own months
        return forecaster.forecast_answer(dataset_id, lang), None
    summary = query_engine.get_summary(dataset_id, parsed["start"], parsed["end"])
    if not summary["has_data"]:                        # no-data message, no chart, no invented numbers
        return rb.t(lang, "no_data", start=parsed["start"], end=parsed["end"]), None

    if intent == "show_chart":
        return chart_maker.build_chart_answer(lang, parsed, summary, message)
    text = rb.build_answer(intent, lang, parsed, summary)
    chart = None
    if intent == "price_trend" and summary["months_used"] >= 2:
        metric = parsed["metric"]
        chart = chart_maker.build_chart(summary, metric,
                                        chart_maker.chart_type_for(metric, message), lang)
    return text, chart


def answer(dataset_id, message):
    """Answer one question for one dataset. Returns a dict for the web page."""
    started = time.time()
    lang = detect_language(message)
    intent, confidence, is_confident = None, 0.0, False
    chart = None
    try:
        if message.strip():
            intent, confidence, is_confident = predict(message)
        reply, chart = _reply_for(dataset_id, message, lang, intent, confidence, is_confident)
        reply = rb.localize_months(lang, reply)
    except Exception:
        traceback.print_exc()                          # show the real error in the terminal
        reply = rb.t(lang, "error")
    try:
        db.save_chat_log(dataset_id, message, intent, confidence, reply, chart)
    except Exception:
        traceback.print_exc()
    return {"reply": reply, "chart": chart, "intent": intent,
            "confidence": round(float(confidence), 3), "language": lang,
            "seconds": round(time.time() - started, 3)}
