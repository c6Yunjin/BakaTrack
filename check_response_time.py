"""TC-18: response time for 20 questions (target: average under 2 seconds).
Uses the same chat engine as the web page. Saves the result as evidence."""
import json
import os
import statistics
import time

import config
from database import db
from modules import chat_engine
from nlp.intent_classifier import predict

QUESTIONS = [
    "hello", "help", "How do I upload data?", "thanks, bye",
    "Ilang kilo ang na-trade noong Hunyo?",
    "Anong buwan pinakamataas ang presyo?",
    "What month had the lowest price?",
    "How many kilos from January to June 2026?",
    "Compare prices of March and June 2026",
    "Compare prices ng March at June 2026",
    "Show cattle prices from January to June 2026",
    "Ipakita ang tsart ng kilos mula Enero hanggang Hunyo 2026",
    "Is the price high or low in October 2026?",
    "Mataas ba o mababa ang presyo ngayong buwan?",
    "forecast next month",
    "Magkano kaya ang presyo sa susunod na buwan?",
    "Price trend for the last 6 months",
    "Ilang ulo ng baka noong Mayo 2026?",
    "What is the weather tomorrow?",
    "Magkano ang presyo noong Hunyo 2030?",
]


def main():
    db.init_db()
    datasets = db.list_datasets()
    if not datasets:
        print("No dataset found. Run: python load_samples.py")
        return
    dataset = datasets[0]
    predict("hello")                                   # load the model first (like app.py does)

    times = []
    for q in QUESTIONS:
        start = time.perf_counter()
        result = chat_engine.answer(dataset["id"], q)
        seconds = time.perf_counter() - start
        times.append(seconds)
        print("{:6.3f}s  [{} | {}]  {}".format(seconds, result["language"], result["intent"], q))

    average = statistics.mean(times)
    summary = {"test": "TC-18", "dataset": dataset["name"], "questions": len(QUESTIONS),
               "average_seconds": round(average, 4), "slowest_seconds": round(max(times), 4),
               "fastest_seconds": round(min(times), 4), "target_seconds": 2.0,
               "passed": average < 2.0}
    out = os.path.join(config.EVIDENCE_DIR, "response_time.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print()
    print("Average {:.3f}s | slowest {:.3f}s | target under 2s -> {}".format(
        average, max(times), "PASS" if summary["passed"] else "FAIL"))
    print("Saved:", out)


main()
