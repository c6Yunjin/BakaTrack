"""Quick terminal test: asks sample questions to the first dataset."""
from database import db
from modules import chat_engine

db.init_db()
dataset_id = db.list_datasets()[0]["id"]
QUESTIONS = [
    "hello",
    "Ilang kilo ang na-trade noong Hunyo?",
    "Anong buwan pinakamataas ang presyo?",
    "Show cattle prices from January to June 2026",
    "How many cattle from March to May 2026?",
    "Compare prices of March and June 2026",
    "Magkano ang presyo noong Hunyo 2030?",
    "Ano ang panahon bukas?",
    "forecast next month",
]
for q in QUESTIONS:
    r = chat_engine.answer(dataset_id, q)
    print("=" * 60)
    print("Q:", q)
    print("[%s | %s | confidence %s | %ss]" % (r["language"], r["intent"], r["confidence"], r["seconds"]))
    print(r["reply"])
