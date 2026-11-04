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
