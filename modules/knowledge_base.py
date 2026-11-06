"""Knowledge base rules (hand-written, no AI model).

Short questions about Padre Garcia ("saan ang baka capital", "kailan ang bakahan") are answered from
data/knowledge_base.json. Every answer shows its source and says it is a general fact, not from the dataset.
A question that mentions prices, kilos, charts, data and so on is NOT taken over: it goes on to the normal flow.
"""
import json
import os
import re

from config import BASE_DIR

KB_PATH = os.path.join(BASE_DIR, "data", "knowledge_base.json")
with open(KB_PATH, encoding="utf-8") as f:
    ENTRIES = json.load(f)["entries"]
INTENTS = {"kb_" + e["id"] for e in ENTRIES}

FILLERS = {"po", "ha", "please", "pls", "plz", "paki", "pakiusap", "nga", "naman", "mo", "kindly"}
BLOCK_WORDS = {"price", "presyo", "kilo", "kilos", "chart", "graph", "forecast", "total", "compare",
               "highest", "lowest", "magkano", "trend", "rating", "rate", "show", "view", "display",
               "ipakita", "pakita", "tingnan", "table", "data", "datos", "records", "summary",
               "buwan", "month", "how", "many", "ilan", "ilang"}
TEXT = {
    "general": {"en": "General fact (not from the loaded data). ",
                "fil": "Pangkalahatang kaalaman (hindi mula sa naka-load na datos). ",
                "taglish": "General fact (hindi galing sa loaded data). "},
    "source": {"en": "Source: ", "fil": "Pinagmulan: ", "taglish": "Source: "},
}


def _words(message):
    text = str(message).lower().replace("'", "").replace("\u2019", "")
    return [w for w in re.findall(r"[a-z0-9\u00f1]+", text) if w not in FILLERS]


def match(message):
    """Returns 'kb_<id>' when a short question fits an entry, else None."""
    words = _words(message)
    if not words or len(words) > 10 or set(words) & BLOCK_WORDS:
        return None
    found = set(words)
    for entry in ENTRIES:
        if found & set(entry.get("exclude", [])):
            continue
        if all(found & set(group) for group in entry["need"]):
            return "kb_" + entry["id"]
    return None


def reply(intent, lang):
    entry = next(e for e in ENTRIES if "kb_" + e["id"] == intent)
    lang = lang if lang in TEXT["general"] else "en"
    answer = entry["answers"].get(lang) or entry["answers"]["en"]
    return "%s%s\n\n%s%s" % (TEXT["general"][lang], answer, TEXT["source"][lang], entry["source"])
