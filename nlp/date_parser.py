# Date and metric parser (rule-based, no AI model).
# Reads a question and finds: the date range (start, end) and the metric
# (total kilos, head count, or price per kilo).
# Phrases like "last 6 months" are counted from the LATEST record in the dataset, not from today.
import re
import calendar
from datetime import date, datetime

from nlp.preprocess import clean_text

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# Every month word we understand (English, Filipino, short forms) -> month number
_MONTH_WORDS = [
    ("january", "jan", "enero", "ene"),
    ("february", "feb", "pebrero", "peb"),
    ("march", "mar", "marso"),
    ("april", "apr", "abril", "abr"),
    ("may", "mayo"),
    ("june", "jun", "hunyo", "hun"),
    ("july", "jul", "hulyo", "hul"),
    ("august", "aug", "agosto"),
    ("september", "sep", "sept", "setyembre", "septyembre"),
    ("october", "oct", "oktubre", "okt"),
    ("november", "nov", "nobyembre", "nob"),
    ("december", "dec", "disyembre"),
]
MONTHS = {word: number for number, words in enumerate(_MONTH_WORDS, start=1) for word in words}

RANGE_WORDS = {"to", "hanggang", "hangang", "until", "through", "thru", "till"}
SINCE_WORDS = {"since", "simula", "mula"}
# "may" is also a Filipino word ("there is"), so it counts as a month only after these words
MAY_OK_BEFORE = {"in", "of", "to", "and", "from", "noong", "hanggang", "kaysa", "or", "o",
                 "than", "between", "vs", "versus", "mula", "until", "through", "since",
                 "simula", "for", "during", "kumpara"}

ISO_DATE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")        # 2026-03-01
SLASH_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")      # 03/01/2026 = month/day/year
N_MONTHS = re.compile(r"\b(?:last|past|nakaraang|huling|nakalipas)\s+(?:na\s+)?(\d{1,2})\s+(?:na\s+)?(?:months?|buwan)\b")
THIS_YEAR = re.compile(r"\b(?:ngayong taon|this year|nitong taon|ngayong year)\b")
LAST_YEAR = re.compile(r"\b(?:nakaraang taon|last year|previous year|nakaraang year)\b")
THIS_MONTH = re.compile(r"\b(?:ngayong buwan|this month|nitong buwan|buwan na ito)\b")
LAST_MONTH = re.compile(r"\b(?:nakaraang buwan|last month|previous month)\b")
NEXT_MONTH = re.compile(r"\b(?:next month|susunod na buwan)\b")

# Metric words (a word matches if it contains one of these)
KILO_WORDS = ("kilo", "timbang", "weight")
PRICE_WORDS = ("presyo", "price", "halaga", "mahal", "mura", "cheap", "expens", "cost")
HEAD_WORDS = ("head", "bilang", "count", "animal")


# ---------- small helpers ----------
def _to_date(value):
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _last_day(year, month):
    return calendar.monthrange(year, month)[1]


def _shift_month(year, month, delta):
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def _describe(start, end):
    """Plain-words version of a date range, for the answer."""
    if start.day == 1 and end.day == _last_day(end.year, end.month):
        a = f"{MONTH_NAMES[start.month - 1]} {start.year}"
        b = f"{MONTH_NAMES[end.month - 1]} {end.year}"
    else:
        a = f"{MONTH_NAMES[start.month - 1]} {start.day}, {start.year}"
        b = f"{MONTH_NAMES[end.month - 1]} {end.day}, {end.year}"
    return a if a == b else f"{a} to {b}"


def _is_day(token):
    return re.fullmatch(r"\d{1,2}", token) is not None and 1 <= int(token) <= 31


def _is_year(token):
    return re.fullmatch(r"(19|20)\d\d", token) is not None


def _add_date(dates, year, month, day):
    try:
        dates.append(date(year, month, day))
    except ValueError:
        pass                      # impossible date like 02/31/2026 is ignored


# ---------- metric ----------
def find_metrics(cleaned):
    """Return the metrics found in the question: price_per_kilo, total_kilos, head_count."""
    tokens = cleaned.split()

    def has(words):
        return any(w in t for t in tokens for w in words)

    found = []
    if has(PRICE_WORDS):
        found.append("price_per_kilo")
    if has(KILO_WORDS):
        found.append("total_kilos")
    if has(HEAD_WORDS):
        found.append("head_count")
    if not found:                 # weak hints, used only when nothing else was found
        if has(("baka",)):
            found.append("head_count")
        elif has(("magkano",)):
            found.append("price_per_kilo")
    return found


# ---------- month names ----------
def _find_month_mentions(tokens):
    """Find month words with an optional day and year next to them."""
    mentions, used = [], set()
    for i, tok in enumerate(tokens):
        if tok not in MONTHS:
            continue
        if tok == "may":
            before = tokens[i - 1] if i > 0 else ""
            after = tokens[i + 1] if i + 1 < len(tokens) else ""
            if before not in MAY_OK_BEFORE and not _is_year(after):
                continue
        day = None
        year_at = i + 1
        if i + 1 < len(tokens) and (i + 1) not in used and _is_day(tokens[i + 1]):
            day = int(tokens[i + 1])
            used.add(i + 1)
            year_at = i + 2
        elif i > 0 and (i - 1) not in used and _is_day(tokens[i - 1]):
            day = int(tokens[i - 1])
            used.add(i - 1)
        year = None
        if year_at < len(tokens) and year_at not in used and _is_year(tokens[year_at]):
            year = int(tokens[year_at])
            used.add(year_at)
        mentions.append({"month": MONTHS[tok], "day": day, "year": year,
                         "since": i > 0 and tokens[i - 1] in SINCE_WORDS})
    return mentions, used


def _resolve_years(mentions, free_year, rel_year, latest):
    """A month without a year uses the nearest year written in the question, else a smart guess."""
    for k, m in enumerate(mentions):
        year = m["year"]
        if year is None:
            later = [x["year"] for x in mentions[k + 1:] if x["year"]]
            earlier = [x["year"] for x in mentions[:k] if x["year"]]
            year = (later[0] if later else None) or (earlier[-1] if earlier else None) or free_year or rel_year
        if year is None:          # no year anywhere: the most recent such month in the data
            year = latest.year if m["month"] <= latest.month else latest.year - 1
        m["resolved"] = year


def _mention_span(m):
    last = _last_day(m["resolved"], m["month"])
    if m["day"]:
        d = date(m["resolved"], m["month"], min(m["day"], last))
        return d, d
    return date(m["resolved"], m["month"], 1), date(m["resolved"], m["month"], last)


def parse_query(text, latest_date=None):
    """Find the date range and metric in a question.
    latest_date = the last date that has records in the active dataset ('YYYY-MM-DD')."""
    latest = _to_date(latest_date)
    latest_end = date(latest.year, latest.month, _last_day(latest.year, latest.month))
    cleaned = clean_text(text)

    # 1. Metric
    metrics = find_metrics(cleaned)
    metric_found = bool(metrics)
    metric = metrics[0] if metrics else "price_per_kilo"

    # 2. Full dates like 2026-03-01 or 03/01/2026 (month/day/year)
    work = cleaned
    dated = []
    for y, mo, d in ISO_DATE.findall(work):
        _add_date(dated, int(y), int(mo), int(d))
    work = ISO_DATE.sub(" ", work)
    for a, b, y in SLASH_DATE.findall(work):
        a, b = int(a), int(b)
        month, day = (b, a) if a > 12 >= b else (a, b)     # 25/12/2026 is read as day/month
        _add_date(dated, int(y), month, day)
    work = SLASH_DATE.sub(" ", work)

    tokens = re.findall(r"[a-zñ]+|\d+", work)
    wants_next_month = bool(NEXT_MONTH.search(work))
    this_year, last_year = bool(THIS_YEAR.search(work)), bool(LAST_YEAR.search(work))
    rel_year = latest.year if this_year else (latest.year - 1 if last_year else None)

    start = end = None
    label = ""
    relative = False
    swapped = False
    months_found = []

    if dated:
        start, end = min(dated), max(dated)
        swapped = len(dated) == 2 and dated[0] > dated[1]
    else:
        mentions, used = _find_month_mentions(tokens)
        free_years = [int(t) for i, t in enumerate(tokens) if i not in used and _is_year(t)]
        free_year = free_years[0] if free_years else None

        if mentions:
            _resolve_years(mentions, free_year, rel_year, latest)
            spans = [_mention_span(m) for m in mentions]
            months_found = [(m["resolved"], m["month"]) for m in mentions]
            if len(mentions) == 1 and mentions[0]["since"]:
                start, end = spans[0][0], latest_end        # "since January"
            else:
                start = min(s[0] for s in spans)
                end = max(s[1] for s in spans)
                swapped = len(mentions) == 2 and spans[0][0] > spans[1][0]
            relative = rel_year is not None and free_year is None and all(m["year"] is None for m in mentions)
        else:
            n_match = N_MONTHS.search(work)
            this_m, last_m = bool(THIS_MONTH.search(work)), bool(LAST_MONTH.search(work))
            if n_match and int(n_match.group(1)) >= 1:
                n = int(n_match.group(1))
                sy, sm = _shift_month(latest.year, latest.month, -(n - 1))
                start, end = date(sy, sm, 1), latest_end
                label, relative = f"the last {n} months", True
            elif last_m or this_m:
                if last_m:
                    ly, lm = _shift_month(latest.year, latest.month, -1)
                    start = date(ly, lm, 1)
                    end = latest_end if this_m else date(ly, lm, _last_day(ly, lm))
                    label = "last month and this month" if this_m else "last month"
                else:
                    start, end, label = date(latest.year, latest.month, 1), latest_end, "this month"
                relative = True
            elif free_year or rel_year:
                year = free_year or rel_year
                start, end = date(year, 1, 1), date(year, 12, 31)
                if free_year:
                    label = f"the year {year}"
                else:
                    label, relative = ("this year" if this_year else "last year"), True

    # 3. Build the notes the answer will show
    notes = []
    range_found = start is not None
    if range_found:
        text_range = _describe(start, end)
        notes.append(f"Showing {label + ': ' if label else ''}{text_range}.")
        if relative:
            notes.append(f"Dates are counted from the latest record in the data ({latest.isoformat()}).")
        if swapped and any(t in RANGE_WORDS for t in tokens):
            notes.append("The dates were in reverse order, so I swapped them.")
    else:
        sy, sm = _shift_month(latest.year, latest.month, -5)
        start, end = date(sy, sm, 1), latest_end
        notes.append(f"No dates were given, so I used the latest 6 months of data: {_describe(start, end)}.")
    if not metric_found:
        notes.append("No metric was given, so I assumed price.")

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "metric": metric,
        "metrics": metrics or [metric],
        "range_found": range_found,
        "metric_found": metric_found,
        "swapped": swapped,
        "months": months_found,
        "wants_next_month": wants_next_month,
        "latest_date": latest.isoformat(),
        "notes": notes,
    }
