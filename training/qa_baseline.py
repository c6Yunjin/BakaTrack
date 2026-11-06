"""Read-only baseline: reworded questions per layer, run on a TEMPORARY copy of the database."""
import os, shutil, tempfile

from database import db

tmp = os.path.join(tempfile.mkdtemp(), "copy.db")
shutil.copy(db.DB_PATH, tmp)
db.DB_PATH = tmp                       # all reads and writes below go to the copy
from modules import chat_engine

M = ["latest_price", "total_value", "price_per_head", "weight_per_head", "market_summary"]
GROUPS = {
    "market": [
        ("can you please tell me what is the most recent price per kilo of cattle in the dataset", ["latest_price"]),
        ("what's the newest price of baka", ["latest_price"]),
        ("ano po ang pinakabagong presyo ng baka sa palengke ngayon", ["latest_price"]),
        ("how much money was made from cattle sales last month in total", ["total_value"]),
        ("what is the overall worth of all the cows that were sold", ["total_value"]),
        ("how heavy is one cow on average", ["weight_per_head"]),
        ("gaano kabigat ang average na baka", ["weight_per_head"]),
        ("how much does one head of cattle cost on average", ["price_per_head"]),
        ("magkano ang average bawat ulo", ["price_per_head"]),
        ("give me a quick overview of the cattle market", ["market_summary"]),
    ],
    "location": [
        ("show data for lipa", ["location_data"]),
        ("i want to see the records from batangas city please", ["location_data"]),
        ("show me data for tanauan", ["location_data"]),
        ("where did this dataset come from", ["location_info"]),
        ("saan galing itong datos na ito", ["location_info"]),
        ("which place is this data about", ["location_info"]),
    ],
    "dataset_info": [
        ("what dates do you have", ["dataset_info"]),
        ("how many records are in this dataset and what is the date range", ["dataset_info"]),
        ("hanggang kailan ang datos mo", ["dataset_info"]),
        ("what is the first and last date of the data", ["dataset_info"]),
    ],
    "data_view": [
        ("show the data for november 2025", None),
        ("can you list the raw records from january to march 2026", None),
        ("pakita mo ang datos ng disyembre 2025", None),
    ],
}
GROUPS["system"] = [(q, ["sys_*"]) for q in [
    "what can you do", "how do you work", "what is your accuracy", "are you using chatgpt",
    "what languages do you understand",
    "how does the forecast work", "ano ang kaya mong gawin", "paano ka gumagana"]]
GROUPS["long"] = [
    ("hi, i am a buyer from lipa and i was wondering if you could tell me, based on the data you have, what was the latest price of cattle per kilo", ["latest_price"]),
    ("kumusta po, gusto ko lang malaman kung ano ang pinakabagong presyo ng baka kasi bibili ako bukas", ["latest_price"]),
    ("good afternoon, can you tell me which place this data is from and also if it is real or sample data", ["location_info"]),
    ("hello po, pwede ko bang malaman kung ano ang kabuuang halaga ng lahat ng baka na nabenta nitong nakaraang buwan", ["total_value"]),
]


def ok(intent, conf, expected):
    if expected is None:
        return intent not in (None, "out_of_scope") and conf >= 0.6
    return any(intent == e or (e.endswith("*") and str(intent).startswith(e[:-1])) for e in expected)


dataset_id = db.list_datasets()[0]["id"]
total = good = 0
for group, items in GROUPS.items():
    g = 0
    print("\n== %s ==" % group)
    for text, expected in items:
        r = chat_engine.answer(dataset_id, text)
        passed = ok(r["intent"], r["confidence"], expected)
        g += passed
        print("%-4s | %-60.60s | %s %.2f" % ("OK" if passed else "FAIL", text, r["intent"], r["confidence"]))
    print("-> %d of %d" % (g, len(items)))
    total += len(items)
    good += g
print("\nTOTAL %d of %d" % (good, total))
