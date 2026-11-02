# ANN intent classifier: loads the trained model and predicts the intent of a message.
import os
import joblib
from config import MODEL_PATH, CONFIDENCE_THRESHOLD
from nlp.preprocess import clean_text

_bundle = None   # the model is loaded once, then reused


def _load():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("Model not found. Train it first: python -m training.train_intent")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def predict(text):
    """Return (intent, confidence, is_confident). Below 60% confidence the bot shows the referral message."""
    cleaned = clean_text(text)
    if not cleaned:
        return "out_of_scope", 0.0, False
    bundle = _load()
    features = bundle["vectorizer"].transform([cleaned])
    probs = bundle["model"].predict_proba(features)[0]
    best = probs.argmax()
    confidence = float(probs[best])
    return str(bundle["model"].classes_[best]), confidence, confidence >= CONFIDENCE_THRESHOLD
