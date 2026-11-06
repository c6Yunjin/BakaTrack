"""Semantic router (hand-written, no pre-trained model).

Runs AFTER all keyword rules and BEFORE the ANN. For questions the keyword rules miss
(new wording, long sentences, synonyms, small typos) it:
  1) strips polite lead-ins ("hi po, can you tell me ...") and filler words
  2) fixes small typos against our own vocabulary and maps synonyms to one standard word
  3) scores the question against our OWN example questions (TF-IDF cosine + word coverage)
  4) answers on a clear match, asks "Did you mean...?" on a weak match, otherwise does nothing
TF-IDF is fitted only on our example sentences.
"""
import difflib
import json
import os
import re

from sklearn.feature_extraction.text import TfidfVectorizer

from config import BASE_DIR
from modules import matching

EXAMPLES_PATH = os.path.join(BASE_DIR, "data", "router_examples.json")
MATCH_AT, NEAR_AT, MARGIN = 0.55, 0.32, 0.08
MAX_WORDS = 45

STOP = set("the a an of in is are to it at po ha ba ay ang ng sa na mga pls please paki nga naman "
           "kindly lang kasi yung yong and also or was were this that have has i my me am if on "
           "per for about with".split())

GROUPS = {
    "baka": "cattle cow cows baka livestock bovine kabaka",
    "market": "market palengke merkado",
    "price": "price prices presyo magkano",
    "kilo": "kilo kilos kg",
    "latest": "latest newest recent current currently now ngayon pinakabago pinakabagong kasalukuyan today presently",
    "value": "value worth revenue cost costs sales sale sell sold halaga benta nabenta nabili earnings income gastos kita",
    "weight": "weight weigh weighs heavy bigat kabigat mabigat timbang",
    "head": "head heads ulo",
    "each": "each kada bawat isa isang one single",
    "average": "average avg mean karaniwan karaniwang",
    "total": "total overall kabuuang kabuuan altogether lahat sum",
    "data": "data dataset datos talaan records record file",
    "place": "place location lugar lokasyon saan saang where province city town bayan",
    "source": "from galing source origin nagmula nanggaling came come collected",
    "date": "date dates petsa",
    "many": "many ilang ilan gaano karaming dami",
    "cover": "cover covers saklaw range span",
    "month": "month months buwan",
    "summary": "summary overview buod",
    "how": "how paano pano",
    "work": "work works working gumagana ginagawa",
    "you": "you your yours yourself ikaw ka mo mong",
    "bot": "bot chatbot bakatrack",
    "accuracy": "accuracy accurate accurately tumpak katumpak katumpakan reliable reliability correct maaasahan",
    "ai": "ai chatgpt gpt openai gemini claude llm api pretrained trained",
    "language": "language languages wika english filipino tagalog taglish",
    "forecast": "forecast forecasting predict prediction hula tantya",
    "rating": "rating rate rated fuzzy",
    "method": "method methods paraan",
    "limit": "limit limits limitation limitations limitasyon cant cannot not trust rely magtiwala",
    "compare": "compare comparison vs versus ihambing hambing kumpara",
    "trend": "trend trends takbo",
    "extreme": "highest lowest peak mataas mababa pinakamataas pinakamababa",
    "chart": "chart graph plot tsart",
}
SYNONYMS = {w: std for std, words in GROUPS.items() for w in words.split()}

MONTHS = set("""january jan february feb march april apr june jun july jul august aug september sep sept
october oct november nov december dec enero pebrero marso abril mayo hunyo hulyo agosto setyembre
oktubre nobyembre disyembre""".split())

BLOCK_DATA = {"forecast", "compare", "trend", "extreme", "chart", "rating"}
BLOCKS = {
    "": set(),
    "data": BLOCK_DATA,
    "loc": BLOCK_DATA | {"upload", "add", "import", "download", "delete", "remove", "how", "change", "edit"},
    "sys": {"baka", "kilo", "chart", "head", "extreme", "compare", "trend", "price", "data", "month"},
}
BLOCKS["sys_how"] = BLOCKS["sys"] | {"forecast", "rating"}
BLOCKS["sys_acc"] = BLOCKS["sys"] | {"forecast"}

LEAD_INS = [
    r"^(?:hi|hello|hey|good (?:morning|afternoon|evening)|kumusta|kamusta|magandang (?:umaga|hapon|gabi|araw))\b[ ,.!]*(?:po\b[ ,.!]*)?",
    r"\bi(?: am|'m|m) an? [a-z]+(?: from [a-z]+(?: city)?)?",
    r"\b(?:can|could|would|will) you (?:please )?(?:tell|show|give|let) me\b",
    r"\bi was wondering (?:if|whether)(?: you (?:could|can))?(?: tell me)?",
    r"\bi (?:would like|want|need) to (?:know|ask)(?: if| about)?",
    r"\bbased on the data you have\b",
    r"\b(?:gusto|nais) ko (?:lang |pong )?(?:malaman|itanong)(?: po)?(?: kung)?",
    r"\bpwede\b(?: \w+){0,3}? (?:malaman|magtanong)(?: po)?(?: kung)?",
    r"\b(?:kasi|dahil|because)\b.*$",
]
DID_YOU_MEAN = {
    "en": 'I am not sure what you mean. Did you mean: "{q}" If so, please ask it again.',
    "fil": 'Hindi ako sigurado sa ibig mong sabihin. Ito ba ang itatanong mo: "{q}" Kung oo, itanong ulit.',
    "taglish": 'Hindi ako sure sa ibig mong sabihin. Did you mean: "{q}" Kung oo, itanong ulit.',
}


def strip_lead_ins(text):
    text = str(text).lower()
    for pattern in LEAD_INS:
        text = re.sub(pattern, " ", text)
    return text


class Router:
    """entries = {id: {intent, need, block, title, examples}}"""

    def __init__(self, entries):
        self.entries = entries
        vocab = set(SYNONYMS)
        for entry in entries.values():
            for sentence in entry["examples"]:
                vocab |= set(matching.tokens(strip_lead_ins(sentence)))
        self.vocab_set = vocab
        self.vocab = sorted(vocab - STOP)
        self.keys, self.sets, docs = [], [], []
        for key, entry in entries.items():
            for sentence in entry["examples"]:
                cleaned = self.clean(sentence)
                self.keys.append(key)
                self.sets.append(set(cleaned.split()))
                docs.append(cleaned)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"\S+", sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(docs)

    def clean(self, text):
        """Strip lead-ins and filler, fix small typos, map synonyms to one standard word."""
        out = []
        for word in matching.tokens(strip_lead_ins(text)):
            if word in STOP:
                continue
            if word not in self.vocab_set and len(word) >= 4:
                close = difflib.get_close_matches(word, self.vocab, n=1, cutoff=0.8)
                if close:
                    word = close[0]
            out.append(SYNONYMS.get(word, word))
        return " ".join(out)

    def decide(self, message):
        """Returns ('match' | 'near' | None, entry id, score)."""
        raw = matching.tokens(message)
        if not raw or len(raw) > MAX_WORDS:
            return None, None, 0.0
        if any(t in MONTHS or re.fullmatch(r"\d{4}", t) for t in raw):   # dated data questions go to the normal flow
            return None, None, 0.0
        cleaned = self.clean(message)
        found = set(cleaned.split())
        if not found:
            return None, None, 0.0
        sims = (self.matrix @ self.vectorizer.transform([cleaned]).T).toarray().ravel()
        best = {}
        for i, key in enumerate(self.keys):
            ex = self.sets[i]
            coverage = len(ex & found) / len(ex) if ex else 0.0       # keeps long sentences from being diluted
            best[key] = max(best.get(key, 0.0), float(sims[i]), 0.9 * coverage * coverage)
        ranked = []
        for key, score in sorted(best.items(), key=lambda kv: kv[1], reverse=True):
            entry = self.entries[key]
            if any(not (found & set(group)) for group in entry.get("need", [])):
                continue
            if found & BLOCKS[entry.get("block", "")]:
                continue
            ranked.append((key, score))
        if not ranked:
            return None, None, 0.0
        key, top = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        if top >= MATCH_AT and top - second >= MARGIN:
            return "match", key, top
        if top >= NEAR_AT:
            return "near", key, top
        return None, None, top


_router = None


def _get():
    global _router
    if _router is None:
        with open(EXAMPLES_PATH, encoding="utf-8") as f:
            _router = Router(json.load(f))
    return _router


def match(message):
    """Returns the intent name for a clear match, else None."""
    kind, key, score = _get().decide(message)
    return _get().entries[key]["intent"] if kind == "match" else None


def near_miss(message, lang):
    """A 'Did you mean...' sentence for a weak match, else None."""
    kind, key, score = _get().decide(message)
    if kind != "near":
        return None
    titles = _get().entries[key]["title"]
    return DID_YOU_MEAN.get(lang, DID_YOU_MEAN["en"]).format(q=titles.get(lang) or titles["en"])
