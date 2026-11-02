# Trains the ANN intent classifier and saves the evidence for the paper.
# Run from the project root:  python -m training.train_intent
import os
import json
from collections import defaultdict

import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")          # draw images without needing a screen
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import FeatureUnion, Pipeline

from config import (INTENTS_PATH, MODEL_PATH, EVIDENCE_DIR, TEST_SIZE,
                    RANDOM_SEED, CONFIDENCE_THRESHOLD)
from nlp.preprocess import prepare
from nlp.intent_classifier import apply_guard

os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)


def make_features():
    """Words (1-2 word groups) plus letter groups (2-4 letters). Letter groups help with Taglish spellings."""
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True)),
    ])


PARAMS = dict(hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
              alpha=1e-4, max_iter=1000, random_state=RANDOM_SEED)

# 1. Load, clean, and remove filler words
with open(INTENTS_PATH, encoding="utf-8") as f:
    intents = json.load(f)["intents"]

owners = defaultdict(set)      # prepared sentence -> which intents contain it
for intent, sentences in intents.items():
    for s in sentences:
        owners[prepare(s)].add(intent)

texts, labels, conflicts = [], [], []
for text, names in owners.items():
    if not text:
        continue
    if len(names) > 1:         # same sentence in 2 intents confuses the ANN, so skip it
        conflicts.append({"sentence": text, "intents": ", ".join(sorted(names))})
    else:
        texts.append(text)
        labels.append(next(iter(names)))

# 2. Split: 80% to learn, 20% hidden for the "exam" (same split every run)
x_train_text, x_test_text, y_train, y_test = train_test_split(
    texts, labels, test_size=TEST_SIZE, random_state=RANDOM_SEED, stratify=labels)

# 3. Words to numbers (TF-IDF learned only from our own training sentences)
vectorizer = make_features()
x_train = vectorizer.fit_transform(x_train_text)
x_test = vectorizer.transform(x_test_text)

# 4. Build and train the ANN: input -> 64 neurons -> 32 neurons -> one output per intent
model = MLPClassifier(**PARAMS)
model.fit(x_train, y_train)

# 5. Quiz it on the hidden sentences: ANN alone, then ANN + market word guard
y_pred = list(model.predict(x_test))
y_system = [apply_guard(t, p) for t, p in zip(x_test_text, y_pred)]
confidence = model.predict_proba(x_test).max(axis=1)
acc_model = accuracy_score(y_test, y_pred)
acc_system = accuracy_score(y_test, y_system)
share_confident = float((confidence >= CONFIDENCE_THRESHOLD).mean())

# 6. Cross-validation: 5 different splits, so the number is steadier than one small test
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
cv_model, cv_system = [], []
for train_idx, test_idx in skf.split(texts, labels):
    pipe = Pipeline([("features", make_features()), ("ann", MLPClassifier(**PARAMS))])
    pipe.fit([texts[i] for i in train_idx], [labels[i] for i in train_idx])
    truth = [labels[i] for i in test_idx]
    pred = list(pipe.predict([texts[i] for i in test_idx]))
    guarded = [apply_guard(texts[i], p) for i, p in zip(test_idx, pred)]
    cv_model.append(accuracy_score(truth, pred))
    cv_system.append(accuracy_score(truth, guarded))

# 7. Save the evidence (per-intent results and confusion matrix use ANN + guard, the real system)
report = pd.DataFrame(classification_report(y_test, y_system, output_dict=True, zero_division=0)).T
report.to_csv(os.path.join(EVIDENCE_DIR, "per_intent_results.csv"))

classes = list(model.classes_)
cm = confusion_matrix(y_test, y_system, labels=classes)
pd.DataFrame(cm, index=classes, columns=classes).to_csv(os.path.join(EVIDENCE_DIR, "confusion_matrix.csv"))

fig, ax = plt.subplots(figsize=(10, 8))
ax.imshow(cm, cmap="Blues")
ax.set_xticks(range(len(classes)))
ax.set_xticklabels(classes, rotation=90)
ax.set_yticks(range(len(classes)))
ax.set_yticklabels(classes)
for i in range(len(classes)):
    for j in range(len(classes)):
        ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8)
ax.set_xlabel("Predicted intent")
ax.set_ylabel("Actual intent")
ax.set_title("Confusion matrix (hidden test sentences)")
fig.tight_layout()
fig.savefig(os.path.join(EVIDENCE_DIR, "confusion_matrix.png"), dpi=150)

pd.DataFrame({"text": x_train_text, "intent": y_train}).to_csv(os.path.join(EVIDENCE_DIR, "train_split.csv"), index=False)
pd.DataFrame({"text": x_test_text, "intent": y_test}).to_csv(os.path.join(EVIDENCE_DIR, "test_split.csv"), index=False)
pd.DataFrame(conflicts, columns=["sentence", "intents"]).to_csv(os.path.join(EVIDENCE_DIR, "removed_duplicates.csv"), index=False)

results = {
    "parameters": PARAMS,
    "features": "TF-IDF: words (1-2 grams) + letters (char_wb 2-4 grams), after removing filler words",
    "random_seed": RANDOM_SEED,
    "total_sentences_used": len(texts),
    "train_size": len(x_train_text),
    "test_size": len(x_test_text),
    "feature_count": int(len(vectorizer.get_feature_names_out())),
    "training_iterations": int(model.n_iter_),
    "test_accuracy_model_only": round(float(acc_model), 4),
    "test_accuracy_with_guard": round(float(acc_system), 4),
    "cv_accuracy_model_only_mean": round(float(np.mean(cv_model)), 4),
    "cv_accuracy_with_guard_mean": round(float(np.mean(cv_system)), 4),
    "cv_accuracy_with_guard_std": round(float(np.std(cv_system)), 4),
    "share_of_test_above_60_percent_confidence": round(share_confident, 4),
    "duplicate_sentences_removed": len(conflicts),
}
with open(os.path.join(EVIDENCE_DIR, "results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# 8. Save the trained model
joblib.dump({"vectorizer": vectorizer, "model": model}, MODEL_PATH)

# 9. Print a summary
print("Sentences used:", len(texts), "| train:", len(x_train_text), "| test:", len(x_test_text))
print("Duplicate sentences removed:", len(conflicts))
print(f"TEST ACCURACY, ANN only:        {acc_model:.2%}")
print(f"TEST ACCURACY, ANN + guard:     {acc_system:.2%}")
print(f"5-FOLD CV, ANN only:            {np.mean(cv_model):.2%}")
print(f"5-FOLD CV, ANN + guard:         {np.mean(cv_system):.2%} (+/- {np.std(cv_system):.2%})")
print(f"Test sentences with confidence >= 60%: {share_confident:.2%}")
print("Per intent (recall, ANN + guard):")
for name in classes:
    print(f"  {name}: {report.loc[name, 'recall']:.2%}")
print("Evidence saved in:", EVIDENCE_DIR)
