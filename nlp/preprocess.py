# Text preprocessing: cleans the user's message before the ANN reads it.
import re

# Spelling variants -> one standard spelling (so the ANN sees the same word)
SPELLING_FIXES = {
    "mag-kano": "magkano", "magkno": "magkano", "mgkano": "magkano", "magkanu": "magkano",
    "presyu": "presyo", "preso": "presyo", "presyo": "presyo",
    "kilos": "kilo", "kg": "kilo", "kgs": "kilo",
    "ilan": "ilan", "ilang": "ilan",
    "baka": "baka", "cattle": "baka", "cow": "baka", "cows": "baka",
    "heads": "head", "ulo": "head",
    "pinaka-mataas": "pinakamataas", "pinaka-mababa": "pinakamababa",
    "ano'ng": "anong", "anung": "anong", "anu": "ano",
    "nung": "noong", "noon": "noong",
    "tlga": "talaga", "po": "", "opo": "", "pls": "please", "plz": "please",
    "chart": "chart", "graph": "chart", "grap": "chart", "tsart": "chart",
    "forcast": "forecast", "prediksyon": "forecast", "hula": "forecast",
}


def clean_text(text):
    """Lowercase, remove extra symbols and spaces, fix common spellings."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s/'-]", " ", text)      # remove symbols like ? ! , .
    text = re.sub(r"\s+", " ", text).strip()     # collapse many spaces into one
    words = [SPELLING_FIXES.get(w, w) for w in text.split()]
    return " ".join(w for w in words if w)


# Filler words that carry no meaning for the intent. Dropped before the ANN reads the text.
STOPWORDS = {
    "ang", "ng", "sa", "na", "ba", "ano", "anong", "ako", "ko", "mo", "ay", "mga",
    "naman", "lang", "din", "rin", "yung", "iyong", "si", "ni", "kay", "para",
    "the", "is", "a", "an", "of", "to", "what", "do", "does", "i", "you", "me",
    "my", "it", "this", "that", "are",
}


def prepare(text):
    """clean_text, then remove filler words. This is what the ANN actually sees."""
    cleaned = clean_text(text)
    words = [w for w in cleaned.split() if w not in STOPWORDS]
    return " ".join(words) if words else cleaned
