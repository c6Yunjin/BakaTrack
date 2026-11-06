"""Location rules (hand-written, no AI model).

Each dataset has one location (a place in Batangas). Questions like "show data for Lipa" or
"where is this data from" are answered from it, and a data question that names a DIFFERENT
place is stopped with an honest message instead of getting this dataset's numbers.
"""
import re

from database import db
from modules import data_view, market_rules, places

INTENT_DATA = "location_data"
INTENT_INFO = "location_info"
INTENTS = {INTENT_DATA, INTENT_INFO}
SCOPED_INTENTS = ({"total_kilos", "head_count", "peak_month", "lowest_month", "price_compare",
                   "price_trend", "show_chart", "forecast", "price_rating"}
                  | market_rules.INTENTS | data_view.INTENTS)

FILLERS = {"po", "ha", "please", "pls", "plz", "paki", "pakiusap", "nga", "naman", "mo", "kindly"}
DATA_WORDS = {"data", "dataset", "records", "record", "datos", "talaan", "table"}
METRIC_WORDS = {"kilo", "kilos", "price", "prices", "presyo", "magkano", "total", "compare", "highest",
                "lowest", "forecast", "trend", "chart", "graph", "rating", "rate", "average", "cost",
                "value", "head", "ulo", "baka", "cattle", "summary"}
PERIOD_WORDS = {"this", "last", "next", "month", "months", "year", "years", "week", "today", "buwan",
                "taon", "ngayong", "nakaraang", "latest"}
MONTHS = {"january", "jan", "february", "feb", "march", "mar", "april", "apr", "may", "june", "jun",
          "july", "jul", "august", "aug", "september", "sep", "sept", "october", "oct", "november",
          "nov", "december", "dec", "enero", "pebrero", "marso", "abril", "mayo", "hunyo", "hulyo",
          "agosto", "setyembre", "oktubre", "nobyembre", "disyembre"}
NOT_A_PLACE = PERIOD_WORDS | MONTHS | {"all", "everything", "lahat", "the", "a", "data", "dataset", "kilos",
                                       "price", "market", "merkado", "palengke", "cattle", "baka", "records"}
INFO_PHRASES = {
    "where is this data from", "where is this dataset from", "where does this data come from",
    "where does the data come from", "where is this from", "what location is this dataset",
    "what is the location of this dataset", "what is the location", "which place is this data from",
    "what place is this data from", "location of this dataset", "dataset location", "data location",
    "where is the data from", "saan galing ang datos", "saan galing ang data", "saan galing ito",
    "saang lugar galing ang datos", "saang lugar galing ang data", "anong lugar ang datos",
    "ano ang lokasyon ng dataset", "ano ang lokasyon",
}
SHOW_RE = re.compile(r"^(?:(?:show|view|display|give|ipakita|pakita|tingnan)(?: me| mo| ang| the)* )?"
                     r"(?:data|dataset|records|datos|talaan|table) "
                     r"(?:for|of|from|in|sa|ng|para sa|mula sa|galing sa) (.+)$")

TEXT = {
    "en": {
        "loc_in": "This dataset is from {label}, so here is its data.",
        "loc_province": "Batangas is a whole province. This dataset covers {label} only, so here is its data (it does not include other Batangas places).",
        "loc_info": "This dataset is from {label}.",
        "loc_sample": " It is SAMPLE (fake) demo data, not real market records.",
        "loc_none_set": "This dataset has no location set. You can choose one when you upload a dataset.",
        "loc_unknown": "I do not know which place this dataset is from, so I cannot tell whether it covers {place}. You can choose a location when you upload a dataset.",
        "loc_out": "This dataset is from {label}. I have no records for {place}.",
        "loc_province_data": "This dataset covers the whole province of Batangas and is not split by place, so I cannot show {place} alone.",
        "loc_other_tab": " The dataset \"{name}\" is from {place}, so try that tab.",
        "loc_no_tab": " No dataset in this app is from {place} yet. You can upload one with the + button and choose its location.",
        "loc_outside": "I only cover places in Batangas.",
        "loc_from": " This dataset is from {label}.",
    },
    "fil": {
        "loc_in": "Ang dataset na ito ay mula sa {label}, kaya narito ang datos nito.",
        "loc_province": "Ang Batangas ay buong lalawigan. Ang dataset na ito ay sumasaklaw lamang sa {label}, kaya narito ang datos nito (hindi kasama ang ibang lugar sa Batangas).",
        "loc_info": "Ang dataset na ito ay mula sa {label}.",
        "loc_sample": " Ito ay SAMPLE (peke) na datos para sa demo, hindi tunay na talaan ng palengke.",
        "loc_none_set": "Walang nakatakdang lokasyon ang dataset na ito. Maaari kang pumili ng isa kapag nag-upload ka ng dataset.",
        "loc_unknown": "Hindi ko alam kung saang lugar galing ang dataset na ito, kaya hindi ko masasabi kung sakop nito ang {place}. Maaari kang pumili ng lokasyon kapag nag-upload ka ng dataset.",
        "loc_out": "Ang dataset na ito ay mula sa {label}. Wala akong talaan para sa {place}.",
        "loc_province_data": "Ang dataset na ito ay sumasaklaw sa buong lalawigan ng Batangas at hindi hinati ayon sa lugar, kaya hindi ko maipapakita ang {place} lamang.",
        "loc_other_tab": " Ang dataset na \"{name}\" ay mula sa {place}, kaya subukan ang tab na iyon.",
        "loc_no_tab": " Wala pang dataset sa app na ito na mula sa {place}. Maaari kang mag-upload gamit ang + button at piliin ang lokasyon.",
        "loc_outside": "Mga lugar lamang sa Batangas ang sakop ko.",
        "loc_from": " Ang dataset na ito ay mula sa {label}.",
    },
    "taglish": {
        "loc_in": "Ang dataset na ito ay mula sa {label}, kaya eto ang data nito.",
        "loc_province": "Ang Batangas ay buong province. Ang dataset na ito ay {label} lang ang sakop, kaya eto ang data nito (hindi kasama ang ibang places sa Batangas).",
        "loc_info": "Ang dataset na ito ay mula sa {label}.",
        "loc_sample": " SAMPLE (fake) demo data ito, hindi totoong market records.",
        "loc_none_set": "Walang location na naka-set ang dataset na ito. Pwede kang pumili ng isa kapag nag-upload ka ng dataset.",
        "loc_unknown": "Hindi ko alam kung saang place galing ang dataset na ito, kaya hindi ko masasabi kung sakop nito ang {place}. Pwede kang pumili ng location kapag nag-upload ka ng dataset.",
        "loc_out": "Ang dataset na ito ay mula sa {label}. Wala akong records para sa {place}.",
        "loc_province_data": "Ang dataset na ito ay sakop ang buong province ng Batangas at hindi hinati per place, kaya hindi ko maipapakita ang {place} lang.",
        "loc_other_tab": " Ang dataset na \"{name}\" ay mula sa {place}, kaya try mo ang tab na iyon.",
        "loc_no_tab": " Wala pang dataset sa app na ito na mula sa {place}. Pwede kang mag-upload gamit ang + button at piliin ang location.",
        "loc_outside": "Mga places lang sa Batangas ang sakop ko.",
        "loc_from": " Ang dataset na ito ay mula sa {label}.",
    },
}


def _say(key, lang, **values):
    return TEXT.get(lang, TEXT["en"])[key].format(**values)


def _norm(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    return " ".join(w for w in re.findall(r"[a-z0-9\u00f1]+", text) if w not in FILLERS)


def _unknown_place(rest):
    """'cebu' -> 'Cebu'. Months, years and plain words are not places."""
    tokens = rest.split()
    if not tokens or len(tokens) > 3:
        return None
    if any(t in NOT_A_PLACE or any(c.isdigit() for c in t) for t in tokens):
        return None
    return rest.title()


def match(message):
    """Returns the location intent, or None when no rule fits."""
    text = _norm(message)
    if not text or len(text.split()) > 10:
        return None
    words = set(text.split())
    place = places.find_place(text)
    if text in INFO_PHRASES:
        return INTENT_INFO
    if place is None and words & {"where", "saan", "saang", "location", "lokasyon", "lugar", "place"} \
            and words & {"data", "dataset", "datos", "talaan", "records"} \
            and words & {"from", "galing", "mula", "ito", "come", "comes"} and not words & METRIC_WORDS:
        return INTENT_INFO
    if place:
        if words & DATA_WORDS and not words & METRIC_WORDS and not words & PERIOD_WORDS \
                and not words & MONTHS and not any(any(c.isdigit() for c in t) for t in words):
            return INTENT_DATA
        return None
    found = SHOW_RE.match(text)
    if found and _unknown_place(found.group(1)):
        return INTENT_DATA
    return None


def scope_text(dataset_id, place, lang):
    """None when this dataset covers the place, else the honest message."""
    if place == places.PROVINCE:
        return None
    loc = db.get_dataset_location(dataset_id)
    if not loc:
        return _say("loc_unknown", lang, place=place)
    if loc == place:
        return None
    if loc == places.PROVINCE:
        return _say("loc_province_data", lang, place=place)
    text = _say("loc_out", lang, label=places.label(loc), place=place)
    for other in db.list_datasets():
        if other["id"] != dataset_id and db.get_dataset_location(other["id"]) == place:
            return text + _say("loc_other_tab", lang, name=other["name"], place=place)
    return text + _say("loc_no_tab", lang, place=place)


def scope_block(dataset_id, message, intent, lang):
    """For data questions: a message when the question names a place this dataset does not cover."""
    if intent not in SCOPED_INTENTS:
        return None
    place = places.find_place(message)
    if place is None or place == places.PROVINCE:
        return None
    return scope_text(dataset_id, place, lang)


def _table(dataset_id, lang):
    try:
        return data_view.reply(dataset_id, "show_data", lang, "show the data")
    except TypeError:
        return data_view.reply(dataset_id, "show_data", lang)


def reply(dataset_id, message, intent, lang):
    """Returns (text, widget) for the two location intents."""
    loc = db.get_dataset_location(dataset_id)
    if intent == INTENT_INFO:
        if not loc:
            return _say("loc_none_set", lang), None
        text = _say("loc_info", lang, label=places.label(loc))
        name = next((d["name"] for d in db.list_datasets() if d["id"] == dataset_id), "")
        if "SAMPLE" in name.upper():
            text += _say("loc_sample", lang)
        return text, None

    place = places.find_place(message)
    if place is None:                                         # a place outside Batangas, like Cebu
        text = _say("loc_outside", lang)
        if loc:
            text += _say("loc_from", lang, label=places.label(loc))
        return text, None
    if place == places.PROVINCE:
        if not loc:
            return _say("loc_none_set", lang), None
        lead = _say("loc_in" if loc == places.PROVINCE else "loc_province", lang, label=places.label(loc))
    else:
        blocked = scope_text(dataset_id, place, lang)
        if blocked:
            return blocked, None
        lead = _say("loc_in", lang, label=places.label(loc))
    text, widget = _table(dataset_id, lang)
    return lead + "\n" + text, widget
