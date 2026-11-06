"""Checks the knowledge base matcher on questions that are NOT in the example list."""
from modules import knowledge_base as kb

POSITIVE = [
    ("what or where is the cattle trading capital in the ph", "capital"),
    ("capital of cattle trading in the philippines", "capital"),
    ("which town is called the cattle capital", "capital"),
    ("cattle trading capital ph", "capital"),
    ("saan po ang cattle trading capital sa pinas", "capital"),
    ("anong bayan ang kabisera ng baka", "capital"),
    ("what is the cattle hub of the philippines", "capital"),
    ("saan yung cattle trading capital sa ph", "capital"),
    ("when did the bakahan begin", "history"),
    ("history of padre garcia cattle market", "history"),
    ("kailan po nagsimula ang bakahan sa padre garcia", "history"),
    ("who founded the bakahan", "history"),
    ("kasaysayan ng cattle trading sa padre garcia", "history"),
    ("what year was the cattle market founded", "history"),
    ("when is the festival of padre garcia", "festival"),
    ("kailan ang kabakahan festival", "festival"),
    ("ano po ang kabakahan festival", "festival"),
    ("what is the cattle festival", "festival"),
    ("what day is the cattle market open", "trading_day"),
    ("kailan ang bentahan ng baka", "trading_day"),
    ("open ba ang bakahan sa friday", "trading_day"),
    ("is the auction every friday", "trading_day"),
    ("anong araw ang bakahan", "trading_day"),
    ("where is the bakahan located", "where"),
    ("saan matatagpuan ang bakahan", "where"),
    ("what province is padre garcia", "where"),
    ("nasaan ang padre garcia", "where"),
    ("capitl of cattle tradng", "capital"),
]
NEGATIVE = [
    "Compare prices of March and June 2026", "price of baka", "Ano ang panahon bukas?",
    "what is the weather in manila", "who is the president of the philippines",
    "where is the nearest mall", "tell me a joke", "capital of france", "hello",
    "show data for batangas", "where is this data from", "saan galing ang data",
    "magkano ang baka ngayon", "forecast next month", "what is the stock market today",
]

hit = near = wrong = 0
print("== should match ==")
for text, fact in POSITIVE:
    got = kb.match(text)
    if got == "kb_" + fact:
        hit += 1
        tag = "HIT "
    elif got is None and kb.near_miss(text, "en"):
        near += 1
        tag = "NEAR"
    else:
        wrong += 1
        tag = "MISS"
    print(tag, "|", text, "->", got)
print("hits %d, near-miss %d, missed or wrong %d of %d" % (hit, near, wrong, len(POSITIVE)))

print("\n== must NOT be taken over ==")
bad = 0
for text in NEGATIVE:
    got = kb.match(text)
    sug = kb.near_miss(text, "en")
    if got:
        bad += 1
    print("TAKEN" if got else ("near " if sug else "ok   "), "|", text, "->", got)
print("wrongly taken over:", bad, "of", len(NEGATIVE))
