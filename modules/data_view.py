"""Data view rules and tables (hand-written, no AI model).

Requests like "show the data" or "show raw records" are matched by plain rules (the same idea as
smalltalk.py). The real numbers are then packed into a table widget for the web page.
Only a WHOLE short message can match, so a real question is never taken over by a rule.
"""
import csv
import io
import re

from database import db
from modules import query_engine as qe
from modules import response_builder as rb

INTENT_MONTHLY = "show_data"
INTENT_RAW = "show_data_raw"
INTENTS = {INTENT_MONTHLY, INTENT_RAW}
RAW_LIMIT = 200            # latest records sent to the page; the CSV download has all of them
FILLERS = {"po", "ha", "please", "pls", "plz", "paki", "pakiusap", "nga", "naman", "mo", "kindly"}

MONTHLY_PHRASES = {
    "show data", "show the data", "show me the data", "show me data", "show my data", "show our data",
    "show table", "show the table", "show me the table", "show data table", "show the data table",
    "show dataset", "show the dataset", "show me the dataset", "view data", "view the data",
    "view dataset", "see the data", "see data", "display data", "display the data", "display table",
    "data table", "monthly table", "monthly summary", "show monthly summary",
    "show the monthly summary", "show monthly data", "show the monthly data",
    "give me the data", "give me the table", "data", "table", "dataset",
    "ipakita ang datos", "ipakita ang data", "ipakita ang talaan", "ipakita ang table",
    "ipakita ang dataset", "pakita ang datos", "pakita ang data", "pakita ang table",
    "tingnan ang datos", "tingnan ang data", "datos", "talaan", "ano ang datos",
    "ano ang laman ng dataset",
}
RAW_PHRASES = {
    "show raw data", "show the raw data", "show raw records", "show the raw records", "raw data",
    "raw records", "show records", "show the records", "show all records", "show all data",
    "view raw data", "view records", "view all records", "raw",
    "ipakita ang raw data", "ipakita ang mga talaan", "ipakita ang lahat ng talaan",
    "ipakita ang mga record", "ipakita ang raw",
}

TEXT = {
    "monthly": {
        "en": "Here is the monthly summary of this dataset: {n} months of records ({first} to {last}), {records} records in total. Click a column heading to sort.",
        "fil": "Narito ang buwanang buod ng dataset na ito: {n} buwan ng talaan ({first} hanggang {last}), {records} talaan sa kabuuan. I-click ang heading ng column para mag-sort.",
        "taglish": "Eto ang monthly summary ng dataset na ito: {n} buwan ng records ({first} hanggang {last}), {records} records in total. I-click ang column heading para mag-sort."},
    "raw_some": {
        "en": "Here are the latest {shown} of {total} raw records (newest first). Use Download CSV to get all of them.",
        "fil": "Narito ang pinakabagong {shown} sa {total} na raw na talaan (pinakabago muna). Gamitin ang Download CSV para makuha ang lahat.",
        "taglish": "Eto ang latest {shown} sa {total} raw records (newest first). Gamitin ang Download CSV para makuha lahat."},
    "raw_all": {
        "en": "Here are all {total} raw records (newest first).",
        "fil": "Narito ang lahat ng {total} na raw na talaan (pinakabago muna).",
        "taglish": "Eto ang lahat ng {total} raw records (newest first)."},
    "title_monthly": {"en": "Monthly summary", "fil": "Buwanang buod", "taglish": "Monthly summary"},
    "title_raw": {"en": "Raw records (newest first)", "fil": "Raw na talaan (pinakabago muna)",
                  "taglish": "Raw records (newest first)"},
}
COLUMNS = {
    "month": {"en": "Month", "fil": "Buwan", "taglish": "Month"},
    "kilos": {"en": "Total kilos", "fil": "Kabuuang kilo", "taglish": "Total kilos"},
    "heads": {"en": "Head count", "fil": "Bilang ng ulo", "taglish": "Head count"},
    "price": {"en": "Price per kilo", "fil": "Presyo kada kilo", "taglish": "Price per kilo"},
    "records": {"en": "Records", "fil": "Talaan", "taglish": "Records"},
    "date": {"en": "Date", "fil": "Petsa", "taglish": "Date"},
}


def _normalize(text):
    text = str(text).lower().replace("'", "").replace("\u2019", "")
    words = re.findall(r"[a-z\u00f1]+", text)
    return " ".join(w for w in words if w not in FILLERS)


def match(message):
    """Returns the data view intent, or None when no rule fits."""
    text = _normalize(message)
    if not text or len(text.split()) > 7:
        return None
    if text in RAW_PHRASES:
        return INTENT_RAW
    if text in MONTHLY_PHRASES:
        return INTENT_MONTHLY
    return None


def _col(key, lang, kind):
    return {"key": key, "label": COLUMNS[key][lang], "type": kind}


def build_monthly(dataset_id, lang):
    """Table widget with one row per month. Returns (text, widget)."""
    summary = qe.get_summary(dataset_id, None, None)
    months = summary["months"]
    rows = [[rb.localize_months(lang, m["label"]), m["total_kilos"], m["head_count"],
             m["price_per_kilo"], m["records"]] for m in months]
    text = TEXT["monthly"][lang].format(n=len(months), first=months[0]["label"], last=months[-1]["label"],
                                        records=summary["records_used"])
    widget = {"widget": "table", "kind": "monthly", "title": TEXT["title_monthly"][lang],
              "columns": [_col("month", lang, "label"), _col("kilos", lang, "kilos"),
                          _col("heads", lang, "int"), _col("price", lang, "price"),
                          _col("records", lang, "int")],
              "rows": rows, "total_rows": len(rows), "page_size": 12,
              "note": rb.t(lang, "price_note"),
              "export_url": "/api/datasets/%d/export.csv?kind=monthly" % dataset_id}
    return text, widget


def build_raw(dataset_id, lang):
    """Table widget with the latest raw records (newest first). Returns (text, widget)."""
    records = db.get_records(dataset_id)
    total = len(records)
    latest = records[-RAW_LIMIT:][::-1]
    rows = [[r["date"], r["head_count"], r["total_kilos"], r["price_per_kilo"]] for r in latest]
    key = "raw_some" if total > len(rows) else "raw_all"
    text = TEXT[key][lang].format(shown=len(rows), total=total)
    widget = {"widget": "table", "kind": "raw", "title": TEXT["title_raw"][lang],
              "columns": [_col("date", lang, "date"), _col("heads", lang, "int"),
                          _col("kilos", lang, "kilos"), _col("price", lang, "price")],
              "rows": rows, "total_rows": total, "page_size": 15, "note": "",
              "export_url": "/api/datasets/%d/export.csv?kind=raw" % dataset_id}
    return text, widget


def reply(dataset_id, intent, lang):
    """Returns (text, widget). An empty dataset gets the normal 'no records yet' message."""
    if db.get_latest_date(dataset_id) is None:
        return rb.t(lang, "empty_dataset"), None
    if intent == INTENT_RAW:
        return build_raw(dataset_id, lang)
    return build_monthly(dataset_id, lang)


def export_csv(dataset_id, kind):
    """The whole dataset as CSV text: kind is 'monthly' or 'raw'."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    if kind == "raw":
        writer.writerow(["date", "head_count", "total_kilos", "price_per_kilo"])
        for r in db.get_records(dataset_id):
            writer.writerow([r["date"], r["head_count"], r["total_kilos"], r["price_per_kilo"]])
    else:
        writer.writerow(["month", "total_kilos", "head_count", "price_per_kilo_weighted", "records"])
        for m in qe.get_summary(dataset_id, None, None)["months"]:
            writer.writerow([m["key"], m["total_kilos"], m["head_count"], m["price_per_kilo"], m["records"]])
    return out.getvalue()


# ---------------------------------------------------------------------------
# Date range for raw records: "show the data for November", "ipakita ang data noong Nobyembre".
# Added below the original functions: each one wraps the original, so the tested code above is unchanged.
# ---------------------------------------------------------------------------
from datetime import datetime

from nlp.date_parser import parse_query

SHOW_WORDS = {"show", "view", "see", "display", "list", "give", "ipakita", "pakita", "tingnan"}
DATA_WORDS = {"data", "datos", "record", "records", "talaan", "table", "dataset", "entries", "rows", "raw"}
# If the message asks for something else (a total, a chart...), it is NOT a data view request
BLOCK_WORDS = {"chart", "graph", "plot", "forecast", "predict", "compare", "kilo", "kilos", "price",
               "presyo", "highest", "lowest", "total", "average", "trend", "how", "many", "ilan",
               "ilang", "magkano", "rate", "rating", "summary", "monthly"}

TEXT.update({
    "range_some": {
        "en": "Here are the latest {shown} of {total} raw records from {start} to {end} (newest first). Use Download CSV to get all of them in this range.",
        "fil": "Narito ang pinakabagong {shown} sa {total} na raw na talaan mula {start} hanggang {end} (pinakabago muna). Gamitin ang Download CSV para makuha ang lahat sa saklaw na ito.",
        "taglish": "Eto ang latest {shown} sa {total} raw records mula {start} hanggang {end} (newest first). Gamitin ang Download CSV para makuha lahat sa range na ito."},
    "range_all": {
        "en": "Here are all {total} raw records from {start} to {end} (newest first).",
        "fil": "Narito ang lahat ng {total} na raw na talaan mula {start} hanggang {end} (pinakabago muna).",
        "taglish": "Eto ang lahat ng {total} raw records mula {start} hanggang {end} (newest first)."},
    "range_none": {
        "en": "There are no records from {start} to {end} in this dataset. Its records run from {first} to {last}.",
        "fil": "Walang talaan mula {start} hanggang {end} sa dataset na ito. Ang mga talaan nito ay mula {first} hanggang {last}.",
        "taglish": "Walang records mula {start} hanggang {end} sa dataset na ito. Ang records nito ay mula {first} hanggang {last}."},
    "title_range": {"en": "Raw records, {start} to {end}", "fil": "Raw na talaan, {start} hanggang {end}",
                    "taglish": "Raw records, {start} to {end}"},
})


def _pretty(iso):
    """'2025-11-01' -> 'November 1, 2025' (the chat engine turns month names into Filipino when needed)."""
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)


def _range_request(message):
    """True for short 'show the data for <dates>' messages (and nothing else)."""
    text = str(message).lower().replace("'", "").replace("\u2019", "")
    tokens = [w for w in re.findall(r"[a-z0-9\u00f1]+", text) if w not in FILLERS]
    if not tokens or len(tokens) > 12:
        return False
    words = set(tokens)
    if not (words & SHOW_WORDS) or not (words & DATA_WORDS) or (words & BLOCK_WORDS):
        return False
    return parse_query(message, None)["range_found"]


_exact_match = match


def match(message):
    """Exact phrases as before, plus 'show the data for November' (raw records of that range)."""
    found = _exact_match(message)
    if found:
        return found
    return INTENT_RAW if _range_request(message) else None


def build_raw_range(dataset_id, lang, start, end):
    """Table widget with the raw records between two dates. Returns (text, widget)."""
    records = db.get_records(dataset_id, start, end)
    nice = {"start": _pretty(start), "end": _pretty(end)}
    if not records:
        every = db.get_records(dataset_id)
        text = TEXT["range_none"][lang].format(first=_pretty(every[0]["date"]),
                                               last=_pretty(every[-1]["date"]), **nice)
        return text, None
    total = len(records)
    latest = records[-RAW_LIMIT:][::-1]
    rows = [[r["date"], r["head_count"], r["total_kilos"], r["price_per_kilo"]] for r in latest]
    text = TEXT["range_some" if total > len(rows) else "range_all"][lang].format(
        shown=len(rows), total=total, **nice)
    widget = {"widget": "table", "kind": "raw",
              "title": rb.localize_months(lang, TEXT["title_range"][lang].format(**nice)),
              "columns": [_col("date", lang, "date"), _col("heads", lang, "int"),
                          _col("kilos", lang, "kilos"), _col("price", lang, "price")],
              "rows": rows, "total_rows": total, "page_size": 15, "note": "",
              "export_url": "/api/datasets/%d/export.csv?kind=raw&start=%s&end=%s" % (dataset_id, start, end)}
    return text, widget


_original_reply = reply


def reply(dataset_id, intent, lang, message=None):
    """Same as before, but a message with dates shows only the records in that range."""
    if intent == INTENT_RAW and message and _range_request(message):
        latest = db.get_latest_date(dataset_id)
        if latest is None:
            return rb.t(lang, "empty_dataset"), None
        parsed = parse_query(message, latest)
        return build_raw_range(dataset_id, lang, parsed["start"], parsed["end"])
    return _original_reply(dataset_id, intent, lang)


_original_export = export_csv
DATE_FORMAT = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def export_csv(dataset_id, kind, start=None, end=None):
    """Whole dataset as before. With start and end (raw only), just the records in that range."""
    if kind == "raw" and start and end and DATE_FORMAT.match(start) and DATE_FORMAT.match(end):
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["date", "head_count", "total_kilos", "price_per_kilo"])
        for r in db.get_records(dataset_id, start, end):
            writer.writerow([r["date"], r["head_count"], r["total_kilos"], r["price_per_kilo"]])
        return out.getvalue()
    return _original_export(dataset_id, kind)
