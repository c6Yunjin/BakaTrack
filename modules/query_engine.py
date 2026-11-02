"""Query engine (Step 5).

Takes the records of ONE dataset and turns them into monthly numbers.
No AI here, just plain arithmetic, so every number can be checked by hand.
"""
from collections import defaultdict

from database import db

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# We tell the user which kind of average we use.
PRICE_METHOD = "weighted by kilos"


def _month_key(date_text):
    """'2026-03-15' -> '2026-03'"""
    return str(date_text)[:7]


def summarize_records(records):
    """Group records by month. Returns a list of monthly rows, oldest first.

    Only months that really have records appear. Missing months are NOT filled in.
    """
    groups = defaultdict(list)
    for r in records:
        groups[_month_key(r["date"])].append(r)

    months = []
    for key in sorted(groups):
        rows = groups[key]
        kilos = sum(r["total_kilos"] for r in rows)
        heads = sum(r["head_count"] for r in rows)
        if kilos > 0:
            # weighted average: heavy trading weeks count more
            price = sum(r["price_per_kilo"] * r["total_kilos"] for r in rows) / kilos
        else:
            price = sum(r["price_per_kilo"] for r in rows) / len(rows)
        year, month = int(key[:4]), int(key[5:7])
        months.append({
            "key": key,
            "year": year,
            "month": month,
            "label": MONTH_NAMES[month - 1] + " " + str(year),
            "total_kilos": round(kilos, 2),
            "head_count": int(heads),
            "price_per_kilo": round(price, 2),
            "records": len(rows),
        })
    return months


def find_gaps(months):
    """List month keys that are missing between the first and last month."""
    if len(months) < 2:
        return []
    have = {m["key"] for m in months}
    y, m = months[0]["year"], months[0]["month"]
    last = (months[-1]["year"], months[-1]["month"])
    gaps = []
    while (y, m) < last:
        key = "%04d-%02d" % (y, m)
        if key not in have:
            gaps.append(key)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return gaps


def get_summary(dataset_id, start, end):
    """Read ONE dataset between two dates and summarize it by month."""
    records = db.get_records(dataset_id, start, end)
    months = summarize_records(records)
    return {
        "has_data": len(months) > 0,
        "start": start,
        "end": end,
        "months": months,
        "months_used": len(months),
        "records_used": len(records),
        "gaps": find_gaps(months),
        "price_method": PRICE_METHOD,
    }


def total_of(summary, metric):
    """Total kilos or total head count over the range."""
    return round(sum(m[metric] for m in summary["months"]), 2)


def average_price(summary):
    """Average price per kilo over the whole range (weighted by kilos)."""
    months = summary["months"]
    kilos = sum(m["total_kilos"] for m in months)
    if kilos > 0:
        return round(sum(m["price_per_kilo"] * m["total_kilos"] for m in months) / kilos, 2)
    return round(sum(m["price_per_kilo"] for m in months) / len(months), 2)


def peak_month(summary, metric):
    """The month with the highest value. Ties go to the earlier month."""
    return max(summary["months"], key=lambda m: m[metric])


def lowest_month(summary, metric):
    """The month with the lowest value. Ties go to the earlier month."""
    return min(summary["months"], key=lambda m: m[metric])


def compare_months(summary, month_a, month_b, metric="price_per_kilo"):
    """Compare two months, each given as (year, month).

    Returns found=False if one of them has no records in the range.
    """
    by_key = {(m["year"], m["month"]): m for m in summary["months"]}
    a, b = by_key.get(month_a), by_key.get(month_b)
    if a is None or b is None:
        missing = [str(k) for k, v in ((month_a, a), (month_b, b)) if v is None]
        return {"found": False, "missing": missing}
    diff = round(b[metric] - a[metric], 2)
    percent = round(diff / a[metric] * 100, 1) if a[metric] else None
    return {"found": True, "a": a, "b": b, "difference": diff, "percent": percent}
