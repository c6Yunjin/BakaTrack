"""Chat engine: follows the project flow chart for ONE question.

preprocess -> intent (ANN) -> 60% rule -> date parser -> no-data check
-> query -> response builder (+ chart) -> save to chat logs.
The dataset_id is passed in every time, so tabs never mix.
"""
import time
import traceback
from modules import market_rules

from database import db
from modules import chart_maker, forecaster, fuzzy_rater, query_engine, response_builder as rb
from nlp.date_parser import parse_query
from modules import knowledge_base, semantic_router, system_facts
from nlp.intent_classifier import predict
from modules import data_view, dataset_info, easter_eggs, location_rules, smalltalk
from nlp.language import detect_language

STATIC_INTENTS = {"greeting", "goodbye", "help", "upload_help", "out_of_scope"}
NOT_READY_INTENTS = set()      # built in later steps


def _reply_for(dataset_id, message, lang, intent, confidence, is_confident):
    """Returns (text, chart). chart is None when there is nothing to draw."""
    if not message.strip():
        return rb.t(lang, "empty_message"), None
    if not is_confident:                               # 60% rule: referral message
        return rb.t(lang, "referral", conf=round(confidence * 100)), None
    if intent in location_rules.INTENTS:               # dataset location questions
        return location_rules.reply(dataset_id, message, intent, lang)
    blocked = location_rules.scope_block(dataset_id, message, intent, lang)
    if blocked:                                        # a place this dataset does not cover
        return blocked, None
    if intent in market_rules.INTENTS:                 # cattle-market rules
        return market_rules.reply(dataset_id, message, intent, lang)
    if intent in easter_eggs.INTENTS:                  # easter egg reply
        return easter_eggs.reply(intent, message, lang)
    if intent in system_facts.INTENTS:                 # facts about this chatbot
        return system_facts.reply(intent, lang), None
    if intent in knowledge_base.INTENTS:                 # Padre Garcia facts with sources
        return knowledge_base.reply(intent, lang), None
    if intent in dataset_info.INTENTS:                 # where this dataset starts and ends
        return dataset_info.reply(dataset_id, lang), None
    if intent in data_view.INTENTS:                    # data table request
        return data_view.reply(dataset_id, intent, lang, message)
    if intent in smalltalk.INTENTS:                    # small talk rule: friendly reply
        return smalltalk.reply(intent, lang), None
    if intent in STATIC_INTENTS:
        return rb.t(lang, intent), None
    if intent in NOT_READY_INTENTS:
        return rb.t(lang, "coming"), None

    latest = db.get_latest_date(dataset_id)
    if latest is None:
        return rb.t(lang, "empty_dataset"), None
    parsed = parse_query(message, latest)
    empty_range = dataset_info.out_of_range(dataset_id, lang, intent, parsed)
    if empty_range:                                    # say where the data really runs
        return empty_range, None
    parsed = dataset_info.use_all_data(dataset_id, lang, intent, parsed)
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
    rule, rule_lang = easter_eggs.match(message), None   # easter eggs first
    if not rule:
        rule, rule_lang = smalltalk.match(message)         # small talk rules come before the ANN
    if not rule:
        rule = location_rules.match(message)    # 'show data for Lipa', 'where is this data from'
    if not rule:
        rule = data_view.match(message)         # 'show the data' requests
    if not rule:
        rule = dataset_info.match(message)      # 'what dates do you have?'
    if not rule:
        rule = market_rules.match(message)       # cattle-market questions the ANN misses
    if not rule:
        rule = knowledge_base.match(message)       # Padre Garcia facts
    if not rule:
        rule = semantic_router.match(message)   # new wordings, long sentences, synonyms, typos
    if rule and rule_lang:
        lang = rule_lang
    intent, confidence, is_confident = None, 0.0, False
    chart = None
    try:
        if rule:
            intent, confidence, is_confident = rule, 1.0, True
        elif message.strip():
            intent, confidence, is_confident = predict(message)
        near = None
        if not rule and message.strip() and (not is_confident or intent == "out_of_scope"):
            near = knowledge_base.near_miss(message, lang) or semantic_router.near_miss(message, lang)     # 'Did you mean...' for unsure matches
        if near:
            intent = "kb_near_miss"
            reply, chart = near, None
        else:
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
