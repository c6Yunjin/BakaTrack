"""Fuzzy price rater (Step 8). Hand-written, no fuzzy library.

Input : price ratio = month average price / overall average price.
Steps : 1) fuzzify  2) fire the rules  3) combine  4) centroid -> score 0..100
"""
from modules import query_engine as qe
from modules import response_builder as rb

MIN_MONTHS = 3        # not enough history -> we do not rate
MAX_RATIO = 2.0       # ratios above this are treated as 2.0

# Each shape is (a, b, c, d): 0 at a, rises to 1 at b, stays 1 until c, falls to 0 at d.
# A triangle is the same shape with b == c.
INPUT_SETS = {                      # shapes over the price ratio
    "low": (0.0, 0.0, 0.85, 0.95),
    "normal": (0.85, 1.0, 1.0, 1.15),
    "high": (1.05, 1.15, 2.0, 2.0),
}
OUTPUT_SETS = {                     # shapes over the price level score 0..100
    "low": (0, 0, 20, 40),
    "normal": (30, 50, 50, 70),
    "high": (60, 80, 100, 100),
}
# Rules: IF price is X THEN level is X (advice comes from the answer templates)
RULES = [("low", "low"), ("normal", "normal"), ("high", "high")]


def membership(x, shape):
    """How much x belongs to a shape: 0 (not at all) to 1 (fully)."""
    a, b, c, d = shape
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if x < b:
        return (x - a) / (b - a)
    return (d - x) / (d - c)


def fuzzify(ratio):
    """Step 1: membership of the ratio in Low, Normal and High."""
    return {name: membership(ratio, shape) for name, shape in INPUT_SETS.items()}


def infer(ratio):
    """Steps 2-4: rule firing (min), combine (max), centroid defuzzification."""
    ratio = max(0.0, min(float(ratio), MAX_RATIO))
    degrees = fuzzify(ratio)
    top, bottom = 0.0, 0.0
    for score in range(0, 101):
        combined = 0.0
        for if_set, then_set in RULES:
            clipped = min(degrees[if_set], membership(score, OUTPUT_SETS[then_set]))
            combined = max(combined, clipped)
        top += score * combined
        bottom += combined
    centroid = top / bottom if bottom else 50.0
    label = max(("low", "normal", "high"), key=lambda k: degrees[k])   # strongest rule wins
    return {"ratio": round(ratio, 3), "memberships": degrees,
            "score": round(centroid, 1), "label": label}


def rate_answer(dataset_id, lang, parsed):
    """Rate one month of ONE dataset against that dataset's own history."""
    summary = qe.get_summary(dataset_id, None, None)
    months = summary["months"]
    if len(months) < MIN_MONTHS:
        return rb.t(lang, "rate_need_more", min=MIN_MONTHS, n=len(months))

    named = parsed.get("months") or []
    if named:
        year, month = named[-1]
        target = next((m for m in months if (m["year"], m["month"]) == (year, month)), None)
        if target is None:
            return rb.t(lang, "rate_no_month", label=qe.MONTH_NAMES[month - 1] + " " + str(year))
    else:
        target = months[-1]

    overall = qe.average_price(summary)
    result = infer(target["price_per_kilo"] / overall)
    pct = abs(result["ratio"] - 1) * 100
    values = dict(label=target["label"], price="{:,.2f}".format(target["price_per_kilo"]),
                  hist="{:,.2f}".format(overall), pct="{:.1f}".format(pct))
    if pct < 0.05:
        main = rb.t(lang, "rate_main_same", **values)
    else:
        main = rb.t(lang, "rate_main_above" if result["ratio"] > 1 else "rate_main_below", **values)
    label = result["label"]
    verdict = rb.t(lang, "rate_result", rating=rb.t(lang, "rating_" + label),
                   score=round(result["score"]), advice=rb.t(lang, "advice_" + label))
    m = result["memberships"]
    footer = rb.t(lang, "rate_footer", n=len(months), first=months[0]["label"],
                  last=months[-1]["label"], low="%.2f" % m["low"],
                  normal="%.2f" % m["normal"], high="%.2f" % m["high"])
    return "\n".join([main, verdict, footer])
