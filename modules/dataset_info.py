"""Dataset info and date-range helpers (hand-written rules, no AI model).

1. "what dates do you have?" -> says where THIS dataset starts and ends.
2. A date range with no records -> says where the data actually runs.
3. "which month is highest?" with no dates -> uses ALL the data of the dataset (not just 6 months).
Everything is read from the active dataset only, so every tab answers from its own dates.
"""
import re

from database import db
from modules import response_builder as rb
from modules.data_view import FILLERS, _pretty
from nlp.date_parser import parse_query

INTENT_INFO = "dataset_info"
INTENTS = {INTENT_INFO}
RANGE_INTENTS = {"total_kilos", "head_count", "peak_month", "lowest_month",
                 "price_compare", "price_trend", "show_chart"}

PHRASES = {
    "what dates do you have", "what dates", "what date range", "what is the date range", "date range",
    "dates", "what is the date range of this dataset", "what dates are in this dataset",
    "what dates does this dataset cover", "how much data do you have", "how much data",
    "how many records", "how many records do you have", "how many months of data",
    "how many months of data do you have", "what data do you have", "what is in this dataset",
    "when does the data start", "when does the data end", "when does this dataset start",
    "when does this dataset end", "when does the data start and end", "start and end date",
    "start and end dates", "first and last date", "first and last dates",
    "saan nagsisimula ang data", "saang petsa nagsisimula ang data", "kailan nagsimula ang data",
    "kailan nagsisimula ang data", "hanggang kailan ang data", "anong mga petsa ang meron ka",
    "anong petsa ang meron ka", "ano ang saklaw ng petsa", "ano ang saklaw ng data",
    "gaano karaming data ang meron ka", "gaano karaming data", "ilan ang records", "ilan ang talaan",
    "ilang buwan ng data ang meron ka", "ilang buwan ng datos",
}
RANGE_HINTS = {"dates", "range", "petsa", "saklaw"}
HAVE_HINTS = {"have", "cover", "covers", "available", "meron"}
EDGE_HINTS = {"start", "starts", "begin", "begins", "end", "ends", "simula", "nagsimula",
              "nagsisimula", "hanggang", "nagtatapos"}
DATA_HINTS = {"data", "dataset", "datos", "records", "record", "talaan"}
QUESTION_HINTS = {"when", "kailan", "saan", "what", "ano", "anong", "hanggang"}
BLOCK_WORDS = {"kilo", "kilos", "price", "presyo", "chart", "graph", "forecast", "total", "compare",
               "highest", "lowest", "magkano", "trend", "rate", "rating", "show", "view", "display",
               "ipakita", "pakita", "tingnan", "table"}

TEXT = {
    "info": {
        "en": "This dataset has {records} records from {first} to {last} ({months} months of data). You can ask about any date in this range.",
        "fil": "Ang dataset na ito ay may {records} na talaan mula {first} hanggang {last} ({months} buwan ng datos). Maaari kang magtanong tungkol sa anumang petsa sa saklaw na ito.",
        "taglish": "Ang dataset na ito ay may {records} records mula {first} hanggang {last} ({months} months ng data). Pwede kang magtanong tungkol sa kahit anong date sa range na ito."},
    "range_none": {
        "en": "There are no records from {start} to {end} in this dataset. Its records run from {first} to {last}. Please try a date inside that range.",
        "fil": "Walang talaan mula {start} hanggang {end} sa dataset na ito. Ang mga talaan nito ay mula {first} hanggang {last}. Pumili ng petsa sa loob ng saklaw na iyon.",
        "taglish": "Walang records mula {start} hanggang {end} sa dataset na ito. Ang records nito ay mula {first} hanggang {last}. Pumili ng date sa loob ng range na iyon."},
    "all_data": {
        "en": "No dates were given, so I used all {months} months of data ({first} to {last}).",
        "fil": "Walang ibinigay na petsa, kaya ginamit ko ang lahat ng {months} buwan ng datos ({first} hanggang {last}).",
        "taglish": "Walang binigay na dates, kaya ginamit ko ang lahat ng {months} months ng data ({first} to {last})."},
}


def _say(key, lang, **values):
    return TEXT[key].get(lang, TEXT[key]["en"]).format(**values)


def span(dataset_id):
    """First date, last date, number of records and months of THIS dataset (None if empty)."""
    records = db.get_records(dataset_id)
    if not records:
        return None
    return {"records": len(records), "first": records[0]["date"], "last": records[-1]["date"],
            "months": len({r["date"][:7] for r in records})}


def _normalize(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    words = re.findall(r"[a-z0-9\u00f1]+", text)
    return " ".join(w for w in words if w not in FILLERS)


def match(message):
    """Returns the dataset info intent for short 'what dates do you have' questions, else None."""
    text = _normalize(message)
    if not text or len(text.split()) > 9:
        return None
    if text in PHRASES:
        return INTENT_INFO
    words = set(text.split())
    if words & BLOCK_WORDS or parse_query(message, None)["range_found"]:
        return None                                   # a real question, or it names a month or year
    if words & RANGE_HINTS and (words & DATA_HINTS or words & HAVE_HINTS):
        return INTENT_INFO
    if words & EDGE_HINTS and words & DATA_HINTS and words & QUESTION_HINTS:
        return INTENT_INFO
    return None


def reply(dataset_id, lang):
    info = span(dataset_id)
    if info is None:
        return rb.t(lang, "empty_dataset")
    return _say("info", lang, records=info["records"], months=info["months"],
                first=_pretty(info["first"]), last=_pretty(info["last"]))


def out_of_range(dataset_id, lang, intent, parsed):
    """A named date range with no records: say where the data really runs. Otherwise None."""
    if intent not in RANGE_INTENTS or not parsed.get("range_found"):
        return None
    info = span(dataset_id)
    if info is None or db.get_records(dataset_id, parsed["start"], parsed["end"]):
        return None
    return _say("range_none", lang, start=_pretty(parsed["start"]), end=_pretty(parsed["end"]),
                first=_pretty(info["first"]), last=_pretty(info["last"]))


def use_all_data(dataset_id, lang, intent, parsed):
    """Highest/lowest month with no dates given: use the whole dataset and say so."""
    if intent not in ("peak_month", "lowest_month") or parsed.get("range_found"):
        return parsed
    info = span(dataset_id)
    if info is None:
        return parsed
    note = _say("all_data", lang, months=info["months"],
                first=_pretty(info["first"]), last=_pretty(info["last"]))
    changed = dict(parsed)
    changed["start"], changed["end"] = info["first"], info["last"]
    notes = [n for n in parsed.get("notes", []) if "latest 6 months" not in n]
    changed["notes"] = [note] + notes
    # the reply builder writes notes from these keys, so swap the old "latest 6 months" key
    range_text = "%s to %s" % (_pretty(info["first"]), _pretty(info["last"]))
    keys = [k for k in parsed.get("note_keys", []) if k[0] != "default_range"]
    keys.insert(0, ("all_data", {"months": info["months"], "range": range_text}))
    changed["note_keys"] = keys
    return changed
