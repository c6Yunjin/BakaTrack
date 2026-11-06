"""Market rules (hand-written, no AI model).

Cattle-market questions the neural network cannot answer well: latest price, total value (cost),
price per head, weight per head and a market summary. Keyword rules decide the question;
the numbers are plain arithmetic on the real records of ONE dataset.
A question that mentions a compare, trend, chart, forecast or rating word is never taken over.
"""
import calendar
import re

from database import db
from modules import data_view
from modules import query_engine as qe
from modules import response_builder as rb
from nlp.date_parser import parse_query

INTENT_LATEST = "latest_price"
INTENT_VALUE = "total_value"
INTENT_PER_HEAD = "price_per_head"
INTENT_WEIGHT = "weight_per_head"
INTENT_SUMMARY = "market_summary"
INTENTS = {INTENT_LATEST, INTENT_VALUE, INTENT_PER_HEAD, INTENT_WEIGHT, INTENT_SUMMARY}

FILLERS = {"po", "ha", "please", "pls", "plz", "paki", "pakiusap", "nga", "naman", "mo", "kindly"}
CATTLE = {"baka", "cattle", "cow", "cows", "kabaka", "livestock", "bovine"}
CONTEXT = CATTLE | {"market", "merkado", "palengke", "trade", "traded", "trading", "sold", "sell", "benta",
                    "nabenta", "sales", "sale", "revenue", "kilos", "kilo", "head", "heads", "ulo"}
TOTAL_WORDS = {"total", "kabuuang", "kabuuan", "overall", "gross"}
VALUE_WORDS = {"cost", "costs", "value", "sales", "sale", "benta", "revenue", "gastos", "halaga",
               "amount", "worth", "price", "prices", "presyo"}
SOLD_WORDS = {"sold", "sell", "traded", "trade", "nabenta", "benta", "nabili"}
EACH_WORDS = {"isang", "bawat", "kada", "each", "one", "single"}
RECENCY = {"latest", "current", "currently", "now", "ngayon", "pinakabago", "pinakabagong", "newest",
           "recent", "today", "kasalukuyan", "presently"}
HARD_EXCLUDE = {"compare", "comparison", "vs", "versus", "trend", "trends", "chart", "graph", "plot",
                "forecast", "predict", "prediction", "hula", "tantya", "rating", "rate", "high", "low",
                "highest", "lowest", "mataas", "mababa", "pinakamataas", "pinakamababa", "peak",
                "hambing", "ihambing", "kumpara", "paghahambing", "bar", "line"}
SHOW_WORDS = {"show", "ipakita", "pakita", "display", "view", "list", "table"}
PERIOD_WORDS = {"month", "months", "monthly", "buwan", "buwanang", "year", "taon", "week", "linggo",
                "quarter", "annual"}
PERIOD_PHRASES = ("this month", "last month", "ngayong buwan", "nakaraang buwan", "nitong buwan",
                  "buwan na ito")
MONTH_WORDS = {"january", "jan", "february", "feb", "march", "mar", "april", "apr", "june", "jun",
               "july", "jul", "august", "aug", "september", "sep", "sept", "october", "oct",
               "november", "nov", "december", "dec", "enero", "pebrero", "marso", "abril", "hunyo",
               "hulyo", "agosto", "setyembre", "oktubre", "nobyembre", "disyembre"}

TEXT = {
    "en": {
        "lp_main": "Latest price in this dataset: {price} per kilo, from the record on {date}. The {label} average is {avg} per kilo.",
        "lp_change": "That is {pct} {direction} than {prev_label} ({prev}).",
        "lp_same": "That is the same as {prev_label} ({prev}).",
        "retail": "This dataset has one price per kilo from the market records; it does not separate retail from wholesale prices.",
        "value": "Total value traded in {label}: {value} (kilos x price). That is {kilos} kg across {heads} heads, at an average of {avg} per kilo.",
        "per_head": "Average price per head in {label}: {pph} ({value} total value / {heads} heads). This is worked out from the records, so it is a rough guide.",
        "weight": "Average weight per head in {label}: {wph} kg ({kilos} kg / {heads} heads).",
        "summary": "Summary for {label}: {kilos} kg traded across {heads} heads, average price {avg} per kilo, total value {value}.",
        "no_heads": "I cannot work that out: the head count in this period is zero.",
        "note_latest_month": "No dates were given, so I used the latest month in the data: {range}.",
    },
    "fil": {
        "lp_main": "Pinakabagong presyo sa dataset na ito: {price} kada kilo, mula sa talaan noong {date}. Ang average ng {label} ay {avg} kada kilo.",
        "lp_change": "Ito ay {pct} {direction} kaysa noong {prev_label} ({prev}).",
        "lp_same": "Pareho ito noong {prev_label} ({prev}).",
        "retail": "Ang dataset na ito ay may iisang presyo kada kilo mula sa talaan ng palengke; hindi nito hinihiwalay ang retail at wholesale.",
        "value": "Kabuuang halaga ng na-trade noong {label}: {value} (kilo x presyo). Ito ay {kilos} kg sa {heads} ulo, may average na {avg} kada kilo.",
        "per_head": "Average na presyo kada ulo noong {label}: {pph} ({value} kabuuang halaga / {heads} ulo). Kinuwenta ito mula sa mga talaan, kaya gabay lamang.",
        "weight": "Average na bigat kada ulo noong {label}: {wph} kg ({kilos} kg / {heads} ulo).",
        "summary": "Buod para sa {label}: {kilos} kg ang na-trade sa {heads} ulo, average na presyo {avg} kada kilo, kabuuang halaga {value}.",
        "no_heads": "Hindi ko ito makuwenta: zero ang bilang ng ulo sa panahong ito.",
        "note_latest_month": "Walang binanggit na petsa, kaya ginamit ko ang pinakabagong buwan sa datos: {range}.",
    },
    "taglish": {
        "lp_main": "Latest price sa dataset na ito: {price} per kilo, mula sa record noong {date}. Ang average ng {label} ay {avg} per kilo.",
        "lp_change": "Mas {direction} ito ng {pct} kaysa noong {prev_label} ({prev}).",
        "lp_same": "Pareho ito noong {prev_label} ({prev}).",
        "retail": "Ang dataset na ito ay may iisang price per kilo mula sa market records; hindi nito hinihiwalay ang retail at wholesale.",
        "value": "Total value na na-trade noong {label}: {value} (kilos x price). {kilos} kg ito sa {heads} heads, average na {avg} per kilo.",
        "per_head": "Average price per head noong {label}: {pph} ({value} total value / {heads} heads). Kinuwenta ito mula sa records, kaya gabay lang.",
        "weight": "Average weight per head noong {label}: {wph} kg ({kilos} kg / {heads} heads).",
        "summary": "Summary para sa {label}: {kilos} kg ang na-trade sa {heads} heads, average price {avg} per kilo, total value {value}.",
        "no_heads": "Hindi ko ito makuwenta: zero ang head count sa period na ito.",
        "note_latest_month": "Walang binanggit na petsa, kaya ginamit ko ang latest month sa data: {range}.",
    },
}
for _lang in TEXT:                       # the parser notes are written by response_builder, so register ours there
    rb.TEXT[_lang]["note_latest_month"] = TEXT[_lang]["note_latest_month"]


def _tokens(message):
    text = str(message).lower().replace("'", "").replace("\u2019", "")
    return [w for w in re.findall(r"[a-z0-9\u00f1]+", text) if w not in FILLERS]


def match(message):
    """Returns a market intent (or 'total_kilos' / 'head_count' for the existing answers), else None."""
    tokens = _tokens(message)
    if not tokens or len(tokens) > 12:
        return None
    words = set(tokens)
    text = " ".join(tokens)
    if words & HARD_EXCLUDE:
        return None

    def starts(prefixes):
        return any(t.startswith(p) for t in tokens for p in prefixes)

    price_word = starts(("price", "presyo")) or "magkano" in words or ("how" in words and "much" in words) \
        or bool(words & {"cost", "costs"})
    cattle = bool(words & CATTLE)
    kilo_word = starts(("kilo", "kg"))
    head_word = bool(words & {"head", "heads", "ulo"})
    period = any(p in text for p in PERIOD_PHRASES)
    has_month = bool(words & MONTH_WORDS) or any(re.fullmatch(r"(19|20)\d\d", t) for t in tokens)

    # total value (cost) of what was traded
    if words & TOTAL_WORDS and words & VALUE_WORDS and words & CONTEXT and "per" not in words:
        return INTENT_VALUE
    if (("how" in words and "much" in words) or "magkano" in words) and words & SOLD_WORDS:
        return INTENT_VALUE
    # price per head and weight per head
    if not kilo_word:
        if price_word and head_word and words & (EACH_WORDS | {"per"}):
            return INTENT_PER_HEAD
        if price_word and cattle and words & EACH_WORDS:
            return INTENT_PER_HEAD
    if starts(("weight", "bigat", "timbang")) and (head_word or (cattle and words & EACH_WORDS)):
        return INTENT_WEIGHT
    # summary or overview
    if words & {"summary", "overview", "buod", "sumaryo", "report"} and \
            (cattle or words & {"market", "merkado", "palengke", "month", "monthly", "buwanang", "dataset", "data", "trading"}):
        return INTENT_SUMMARY
    # "kilos of baka this month" and "how many baka this month" use the existing answers
    if cattle and period and not price_word:
        if kilo_word:
            return "total_kilos"
        if words & {"ilang", "ilan", "bilang"} or ("how" in words and "many" in words) or head_word:
            return "head_count"
    # latest price
    if price_word and not has_month and not (words & PERIOD_WORDS):
        if words & RECENCY:
            return INTENT_LATEST
        if cattle and len(tokens) <= 6 and not (words & SHOW_WORDS):
            return INTENT_LATEST
    return None


# ---------- the answers ----------
def _fmt(key, lang, **values):
    return TEXT[lang][key].format(**values)


def _money(value):
    return "\u20b1{:,.2f}".format(value)


def _weighted_price(records):
    kilos = sum(r["total_kilos"] for r in records)
    if kilos > 0:
        return sum(r["price_per_kilo"] * r["total_kilos"] for r in records) / kilos
    return sum(r["price_per_kilo"] for r in records) / len(records)


def _date_label(iso):
    return "%s %d, %d" % (qe.MONTH_NAMES[int(iso[5:7]) - 1], int(iso[8:10]), int(iso[:4]))


def _period(message, latest):
    """The period the question asks about. No date in the question means the latest month."""
    parsed = parse_query(message, latest)
    if not parsed["range_found"]:
        y, m = int(latest[:4]), int(latest[5:7])
        parsed["start"] = "%04d-%02d-01" % (y, m)
        parsed["end"] = "%04d-%02d-%02d" % (y, m, calendar.monthrange(y, m)[1])
        label = qe.MONTH_NAMES[m - 1] + " " + str(y)
        parsed["note_keys"] = [k for k in parsed.get("note_keys", []) if k[0] != "default_range"] + \
                              [("latest_month", {"range": label})]
    return parsed


def _period_label(lang, summary):
    months = summary["months"]
    first, last = months[0]["label"], months[-1]["label"]
    if first == last:
        return first
    return first + (" to " if lang == "en" else " hanggang ") + last


def _latest_price(dataset_id, message, lang, latest):
    months = qe.get_summary(dataset_id, None, None)["months"]
    month = months[-1]
    day_price = _weighted_price(db.get_records(dataset_id, latest, latest))
    lines = [_fmt("lp_main", lang, price=_money(day_price), date=_date_label(latest),
                  label=month["label"], avg=_money(month["price_per_kilo"]))]
    if len(months) >= 2 and months[-2]["price_per_kilo"]:
        prev = months[-2]
        diff = round(month["price_per_kilo"] - prev["price_per_kilo"], 2)
        if diff == 0:
            lines.append(_fmt("lp_same", lang, prev_label=prev["label"], prev=_money(prev["price_per_kilo"])))
        else:
            pct = diff / prev["price_per_kilo"] * 100
            lines.append(_fmt("lp_change", lang, pct=rb.fmt_percent(pct),
                              direction=rb.t(lang, "up" if diff > 0 else "down"),
                              prev_label=prev["label"], prev=_money(prev["price_per_kilo"])))
    summary = {"months": [month], "months_used": 1, "gaps": []}
    footer = rb._footer_line(lang, {"note_keys": []}, summary, "price_per_kilo")
    if "retail" in _tokens(message):
        footer += " " + TEXT[lang]["retail"]
    return "\n".join(lines) + "\n\n" + footer


def reply(dataset_id, message, intent, lang):
    """Returns (text, widget) for one market intent, using ONLY this dataset's records."""
    latest = db.get_latest_date(dataset_id)
    if latest is None:
        return rb.t(lang, "empty_dataset"), None
    if intent == INTENT_LATEST:
        return _latest_price(dataset_id, message, lang, latest), None
    if intent == INTENT_SUMMARY and not parse_query(message, latest)["range_found"]:
        return data_view.build_monthly(dataset_id, lang)          # no period given: the monthly table

    parsed = _period(message, latest)
    summary = qe.get_summary(dataset_id, parsed["start"], parsed["end"])
    if not summary["has_data"]:
        return rb.t(lang, "no_data", start=parsed["start"], end=parsed["end"]), None
    records = db.get_records(dataset_id, parsed["start"], parsed["end"])
    kilos = sum(r["total_kilos"] for r in records)
    heads = int(sum(r["head_count"] for r in records))
    value = sum(r["price_per_kilo"] * r["total_kilos"] for r in records)
    label = _period_label(lang, summary)
    footer = rb._footer_line(lang, parsed, summary, "total_kilos")
    kilos_text, heads_text = "{:,.0f}".format(kilos), "{:,}".format(heads)

    if intent in (INTENT_PER_HEAD, INTENT_WEIGHT) and heads <= 0:
        return _fmt("no_heads", lang) + "\n\n" + footer, None
    if intent == INTENT_VALUE:
        text = _fmt("value", lang, label=label, value=_money(value), kilos=kilos_text, heads=heads_text,
                    avg=_money(_weighted_price(records)))
    elif intent == INTENT_PER_HEAD:
        text = _fmt("per_head", lang, label=label, pph=_money(value / heads), value=_money(value), heads=heads_text)
    elif intent == INTENT_WEIGHT:
        text = _fmt("weight", lang, label=label, wph="{:,.1f}".format(kilos / heads), kilos=kilos_text, heads=heads_text)
    else:
        text = _fmt("summary", lang, label=label, kilos=kilos_text, heads=heads_text,
                    avg=_money(_weighted_price(records)), value=_money(value))
    return text + "\n\n" + footer, None
