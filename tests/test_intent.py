# Step 3 checks: accuracy target, a known question, TC-14, and the market word guard.
import json
import os
from config import EVIDENCE_DIR
from nlp.intent_classifier import predict, apply_guard


def test_accuracy_target():
    with open(os.path.join(EVIDENCE_DIR, "results.json")) as f:
        results = json.load(f)
    assert results["test_accuracy_with_guard"] >= 0.80


def test_known_question():
    intent, confidence, ok = predict("Anong buwan pinakamataas ang presyo?")
    assert intent == "peak_month"


def test_tc14_out_of_scope():
    intent, confidence, ok = predict("Ano ang panahon bukas?")
    assert intent == "out_of_scope" or not ok


def test_guard_rules():
    assert apply_guard("panahon bukas", "price_trend") == "out_of_scope"   # no market word
    assert apply_guard("presyo buwan", "price_trend") == "price_trend"      # has market words
    assert apply_guard("hello", "greeting") == "greeting"                   # not a data intent
