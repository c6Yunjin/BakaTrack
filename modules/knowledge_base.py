"""Knowledge base rules (hand-written, no AI model).

Short questions about Padre Garcia ("saan ang baka capital", "kailan ang bakahan") are answered from
data/knowledge_base.json. Every answer shows its source and says it is a general fact, not from the dataset.
A question that mentions prices, kilos, charts, data and so on is NOT taken over: it goes on to the normal flow.
"""
import json
import os
import re

from config import BASE_DIR
from modules import matching

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


def _keyword_match(message):
    """Returns 'kb_<id>' when a short question fits an entry, else None."""
    words = _words(message)
    if not words or len(words) > 16 or set(words) & BLOCK_WORDS:
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


# ---- similarity matching (handles new wordings, synonyms and small typos) ----
EXAMPLES_PATH = os.path.join(BASE_DIR, "data", "kb_examples.json")
TOPIC_WORDS = {"baka", "padre", "garcia", "batangas", "market", "trading", "festival", "friday"}
DID_YOU_MEAN = {
    "en": 'I am not sure what you mean. Did you mean: "{q}" If so, please ask it again.',
    "fil": 'Hindi ako sigurado sa ibig mong sabihin. Ito ba ang itatanong mo: "{q}" Kung oo, itanong ulit.',
    "taglish": 'Hindi ako sure sa ibig mong sabihin. Did you mean: "{q}" Kung oo, itanong ulit.',
}
_matcher = None


def _get_matcher():
    global _matcher
    if _matcher is None:
        with open(EXAMPLES_PATH, encoding="utf-8") as f:
            _matcher = matching.Matcher(json.load(f), TOPIC_WORDS)
    return _matcher


def _blocked(message):
    words = _words(message)
    return (not words) or len(words) > 25 or bool(set(words) & BLOCK_WORDS)


def match(message):
    """Returns 'kb_<id>' for a clear match (new wording or old keywords), else None."""
    if _blocked(message):
        return None
    kind, key, score = _get_matcher().decide(message)
    if kind == "match":
        return "kb_" + key
    return _keyword_match(message)


def near_miss(message, lang):
    """A 'Did you mean...' sentence when the match is uncertain, else None."""
    if _blocked(message) or match(message):
        return None
    kind, key, score = _get_matcher().decide(message)
    if kind != "near":
        return None
    titles = _get_matcher().titles[key]
    question = titles.get(lang) or titles["en"]
    return DID_YOU_MEAN.get(lang, DID_YOU_MEAN["en"]).format(q=question)
