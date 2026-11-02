# Tests the trained model on questions written by classmates (the honest accuracy).
# Fill data/classmate_questions.csv first. Run:  python -m training.eval_classmates
import os
import pandas as pd
from config import BASE_DIR
from nlp.intent_classifier import predict

df = pd.read_csv(os.path.join(BASE_DIR, "data", "classmate_questions.csv")).dropna()
if df.empty:
    raise SystemExit("data/classmate_questions.csv has no rows yet.")

correct = 0
for row in df.itertuples():
    intent, confidence, ok = predict(row.text)
    hit = intent == row.intent
    correct += hit
    print(("OK   " if hit else "WRONG"), f"{confidence:.0%}", "|", row.text, "->", intent, "(expected", row.intent + ")")
print(f"\nClassmate accuracy: {correct}/{len(df)} = {correct / len(df):.2%}")
