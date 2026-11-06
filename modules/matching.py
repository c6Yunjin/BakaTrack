"""Shared matcher (hand-written, no pre-trained model).

Steps: clean the question, fix small typos, map synonyms to one standard word,
then compare it with OUR OWN example questions (TF-IDF + cosine similarity).
TF-IDF is fitted ONLY on our example sentences.
"""
import difflib
import re

from sklearn.feature_extraction.text import TfidfVectorizer

STOP = set("the a an of in is are to it at po ha ba ay ang ng sa na mga pls please paki nga "
           "naman mo ko yung yong do does you me can tell i my there for".split())

GROUPS = {
    "baka": "cattle cow cows baka bakahan livestock",
    "capital": "capital kabisera hub center centre heart famous kilala",
    "trading": "trading trade trades traded bentahan bilihan auction bidding sale sell selling",
    "market": "market palengke merkado",
    "start": "start started starts begin began beginning founded established itinatag "
             "nagsimula simula origin origins history kasaysayan nagmula",
    "festival": "festival fiesta pista kabakahan celebration selebrasyon",
    "when": "when kailan kelan kaylan",
    "where": "where saan nasaan located location matatagpuan province probinsya",
    "friday": "friday fridays biyernes",
    "schedule": "schedule iskedyul araw day days weekly every tuwing bawat time oras open bukas",
    "philippines": "philippines pilipinas pinas ph",
}
SYNONYMS = {w: standard for standard, words in GROUPS.items() for w in words.split()}


def tokens(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    return re.findall(r"[a-z0-9\u00f1]+", text)


class Matcher:
    """entries = {id: {"examples": [...], "core": [...], "title": {...}}}"""

    def __init__(self, entries, topic, match_at=0.50, near_at=0.28, margin=0.06):
        self.topic = set(topic)
        self.match_at, self.near_at, self.margin = match_at, near_at, margin
        self.core = {k: set(v.get("core", [])) for k, v in entries.items()}
        self.titles = {k: v.get("title", {}) for k, v in entries.items()}
        words = set(SYNONYMS)
        self.keys, docs = [], []
        for key, entry in entries.items():
            for sentence in entry["examples"]:
                self.keys.append(key)
                docs.append(sentence)
                words |= set(tokens(sentence))
        self.vocab_set = words - STOP
        self.vocab = sorted(self.vocab_set)
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"\S+", sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([self.clean(d) for d in docs])

    def clean(self, text):
        """Lowercase, drop filler words, fix small typos, map synonyms."""
        out = []
        for word in tokens(text):
            if word in STOP:
                continue
            if word not in self.vocab_set and len(word) >= 4:
                close = difflib.get_close_matches(word, self.vocab, n=1, cutoff=0.8)
                if close:
                    word = close[0]
            out.append(SYNONYMS.get(word, word))
        return " ".join(out)

    def score(self, message):
        """Best similarity (0 to 1) per entry, highest first."""
        query = self.vectorizer.transform([self.clean(message)])
        sims = (self.matrix @ query.T).toarray().ravel()
        best = {}
        for key, value in zip(self.keys, sims):
            best[key] = max(best.get(key, 0.0), float(value))
        return sorted(best.items(), key=lambda kv: kv[1], reverse=True)

    def decide(self, message):
        """Returns ('match' | 'near' | None, entry id, score)."""
        found = set(self.clean(message).split())
        if not found & self.topic:                       # nothing about our topic
            return None, None, 0.0
        ranked = [(k, s) for k, s in self.score(message)
                  if not self.core[k] or found & self.core[k]]
        if not ranked:
            return None, None, 0.0
        key, best = ranked[0]
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        if best >= self.match_at and best - second >= self.margin:
            return "match", key, best
        if best >= self.near_at:
            return "near", key, best
        return None, None, best
