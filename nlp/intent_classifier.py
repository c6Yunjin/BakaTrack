# ANN intent classifier: loads the trained model and predicts the intent of a message.
# Includes a simple hand-written "market word guard" (see apply_guard).
import os
import joblib
from config import MODEL_PATH, CONFIDENCE_THRESHOLD
from nlp.preprocess import prepare

_bundle = None   # the model is loaded once, then reused

# Intents that need cattle-market data to answer
DATA_INTENTS = {"total_kilos", "head_count", "peak_month", "lowest_month", "price_compare",
                "price_trend", "show_chart", "forecast", "price_rating"}

# Words that show the question is about the market (a word matches if it starts with one of these)
MARKET_WORDS = (
    "baka", "kilo", "timbang", "weight", "presyo", "price", "magkano", "buwan", "month",
    "chart", "forecast", "predict", "trend", "taon", "year", "auction", "benta", "trade",
    "sell", "buy", "bili", "bumili", "bibili", "mura", "mahal", "cheap", "expens", "mataas",
    "mababa", "high", "low", "compar", "hambing", "kumpara", "peak", "total", "bilang",
    "head", "ilan", "tumata", "bumaba", "pataas", "pababa", "rising", "increas", "decreas",
    "tantya", "inaasahan", "expected", "projected", "estimate", "future", "volume",
    "enero", "pebrero", "marso", "abril", "mayo", "hunyo", "hulyo", "agosto", "setyembre",
    "oktubre", "nobyembre", "disyembre", "january", "february", "march", "april", "june",
    "july", "august", "september", "october", "november", "december",
)


def has_market_word(text):
    for token in text.split():
        for word in MARKET_WORDS:
            if token.startswith(word) or (len(word) >= 5 and word in token):
                return True
    return False


def apply_guard(prepared_text, intent):
    """If the ANN picked a data intent but the message has no market word, it is out of scope."""
    if intent in DATA_INTENTS and not has_market_word(prepared_text):
        return "out_of_scope"
    return intent


def _load():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Model not found. Train it first: python -m training.train_intent")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def predict(text):
    """Return (intent, confidence, is_confident). Below 60% confidence the bot shows the referral message."""
    prepared = prepare(text)
    if not prepared:
        return "out_of_scope", 0.0, False
    bundle = _load()
    features = bundle["vectorizer"].transform([prepared])
    probs = bundle["model"].predict_proba(features)[0]
    best = probs.argmax()
    confidence = float(probs[best])
    model_intent = str(bundle["model"].classes_[best])
    intent = apply_guard(prepared, model_intent)
    is_confident = confidence >= CONFIDENCE_THRESHOLD or intent != model_intent
    return intent, confidence, is_confident
