# Step 3 checks: accuracy target, a known question, and TC-14 (out-of-scope question).
import json
import os
from config import EVIDENCE_DIR
from nlp.intent_classifier import predict


def test_accuracy_target():
    with open(os.path.join(EVIDENCE_DIR, "results.json")) as f:
        results = json.load(f)
    assert results["test_accuracy"] >= 0.85


def test_known_question():
    intent, confidence, ok = predict("Anong buwan pinakamataas ang presyo?")
    assert intent == "peak_month"


def test_tc14_out_of_scope():
    intent, confidence, ok = predict("Ano ang panahon bukas?")
    assert intent == "out_of_scope" or not ok
