"""Read-only stress test: unseen wordings, locations, near misses and must-not-steal questions."""
import os, shutil, tempfile

from database import db

tmp = os.path.join(tempfile.mkdtemp(), "copy.db")
shutil.copy(db.DB_PATH, tmp)
db.DB_PATH = tmp
from modules import chat_engine

DATA = ["total_kilos", "head_count", "peak_month", "lowest_month", "price_compare", "price_trend",
        "show_chart", "forecast", "price_rating", "out_of_scope"]
T = [
    ("show data for lipa city please", ["location_data"]),
    ("can i see the records for batangas", ["location_data"]),
    ("i would like to know the place where this dataset was taken from", ["location_info"]),
    ("is the data you have from a real market or just made up", ["location_info", "sys_limits"]),
    ("what's the current going rate for cattle per kilo", ["latest_price"]),
    ("bale magkano na ang kilo ng baka ngayon sa market", ["latest_price"]),
    ("what was the total amount of money from all the cows sold last month", ["total_value"]),
    ("on average how many kilos does a single head weigh", ["weight_per_head"]),
    ("how big is the dataset", ["dataset_info"]),
    ("what period of time does your data go back to", ["dataset_info"]),
    ("are you reliable", ["sys_accuracy", "sys_limits"]),
    ("did you use any pretrained model to learn", ["sys_ai"]),
    ("hello there, could you explain to me how this whole chatbot works behind the scenes", ["sys_how"]),
    ("tell me what you are capable of doing for me", ["sys_about"]),
    ("saan po ba yung capital ng cattle trading dito sa pilipinas", ["kb_capital"]),
    ("kelan po ba yung bakahan sa padre garcia, bibili kasi ako", ["kb_trading_day"]),
    ("what's the story behind the padre garcia cattle market", ["kb_history"]),
    ("Compare prices of March and June 2026", DATA),
    ("how many cattle from march to may 2026", DATA),
    ("forecast the price for next month", DATA),
    ("what is the price rating for october 2026", ["price_rating"]),
    ("show me a line chart of prices from january to june", DATA),
    ("what is the weather today", ["out_of_scope"]),
    ("who is the president of the philippines", ["out_of_scope"]),
    ("recommend a good restaurant in lipa", ["out_of_scope"]),
    ("how do i make adobo", ["out_of_scope"]),
]
dataset_id = db.list_datasets()[0]["id"]
good = 0
for text, expected in T:
    r = chat_engine.answer(dataset_id, text)
    ok = r["intent"] in expected
    good += ok
    print("%-4s | %-62.62s | %s %.2f" % ("OK" if ok else "FAIL", text, r["intent"], r["confidence"]))
    if r["intent"] == "kb_near_miss":
        print("       near miss ->", r["reply"][:110])
print("\nTOTAL %d of %d" % (good, len(T)))
