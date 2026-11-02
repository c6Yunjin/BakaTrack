# Trains the ANN intent classifier and saves the evidence for the paper.
# Run from the project root:  python -m training.train_intent
import os
import json
from collections import defaultdict

import joblib
import matplotlib
matplotlib.use("Agg")          # draw images without needing a screen
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier

from config import (INTENTS_PATH, MODEL_PATH, EVIDENCE_DIR, TEST_SIZE,
                    RANDOM_SEED, CONFIDENCE_THRESHOLD)
from nlp.preprocess import clean_text

os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

# 1. Load and clean the sentences
with open(INTENTS_PATH, encoding="utf-8") as f:
    intents = json.load(f)["intents"]

owners = defaultdict(set)      # cleaned sentence -> which intents contain it
for intent, sentences in intents.items():
    for s in sentences:
        owners[clean_text(s)].add(intent)

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

# 3. Turn words into numbers (TF-IDF, learned only from our own training sentences)
vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
x_train = vectorizer.fit_transform(x_train_text)
x_test = vectorizer.transform(x_test_text)

# 4. Build and train the ANN: input -> 64 neurons -> 32 neurons -> one output per intent
params = dict(hidden_layer_sizes=(64, 32), activation="relu", solver="adam",
              alpha=1e-4, max_iter=1000, random_state=RANDOM_SEED)
model = MLPClassifier(**params)
model.fit(x_train, y_train)

# 5. Quiz it on the hidden sentences
y_pred = model.predict(x_test)
confidence = model.predict_proba(x_test).max(axis=1)
accuracy = accuracy_score(y_test, y_pred)
share_confident = float((confidence >= CONFIDENCE_THRESHOLD).mean())

# 6. Save the evidence
report = pd.DataFrame(classification_report(y_test, y_pred, output_dict=True, zero_division=0)).T
report.to_csv(os.path.join(EVIDENCE_DIR, "per_intent_results.csv"))

classes = list(model.classes_)
cm = confusion_matrix(y_test, y_pred, labels=classes)
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
    "parameters": params,
    "vectorizer": "TF-IDF, word 1-2 grams, sublinear_tf",
    "random_seed": RANDOM_SEED,
    "total_sentences_used": len(texts),
    "train_size": len(x_train_text),
    "test_size": len(x_test_text),
    "vocabulary_size": len(vectorizer.vocabulary_),
    "training_iterations": int(model.n_iter_),
    "test_accuracy": round(float(accuracy), 4),
    "share_of_test_above_60_percent_confidence": round(share_confident, 4),
    "duplicate_sentences_removed": len(conflicts),
}
with open(os.path.join(EVIDENCE_DIR, "results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# 7. Save the trained model
joblib.dump({"vectorizer": vectorizer, "model": model}, MODEL_PATH)

# 8. Print a summary
print("Sentences used:", len(texts), "| train:", len(x_train_text), "| test:", len(x_test_text))
print("Duplicate sentences removed:", len(conflicts))
print(f"TEST ACCURACY: {accuracy:.2%}")
print(f"Test sentences with confidence >= 60%: {share_confident:.2%}")
print("Per intent (recall):")
for name in classes:
    print(f"  {name}: {report.loc[name, 'recall']:.2%}")
print("Evidence saved in:", EVIDENCE_DIR)
