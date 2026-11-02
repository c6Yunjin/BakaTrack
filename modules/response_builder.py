"""Response builder (Step 6).

Pre-written sentence templates (English and Filipino). The code only fills in
the REAL numbers from the query engine. No AI writes the answers.
"""
from modules import query_engine as qe

TEXT = {
    "en": {
        "greeting": "Hello! I am BakaTrack. Ask me about cattle kilos, head count and prices from the data in this tab.",
        "goodbye": "Goodbye! Please confirm important decisions with the market office.",
        "help": "You can ask me: total kilos, how many cattle (head count), the highest or lowest month, a price comparison between two months, and price trends. Example: \"Show prices from January to June 2026\".",
        "upload_help": "To add data, click the + button and upload a CSV with these columns: date (YYYY-MM-DD), head_count, total_kilos, price_per_kilo. If something is wrong I will tell you and nothing will be saved.",
        "out_of_scope": "Sorry, I can only answer questions about cattle volume and prices from the loaded data.",
        "referral": "I am not sure I understood that (confidence {conf}%). Please rephrase it, or ask the market administration or the Municipal Agriculture Office.",
        "no_data": "No records found from {start} to {end} in this tab, so I cannot answer. Please try another date range.",
        "empty_dataset": "This tab has no records yet. Please upload a CSV with the + button.",
        "empty_message": "Please type a question.",
        "error": "Sorry, something went wrong on my side. Please try again.",
        "coming": "This feature is not available yet in this version.",
        "range_line": "Showing {start} to {end}: {n} month(s) of records used.",
        "total_line": "{name}: {value}",
        "peak_line": "Highest {name}: {label} ({value}).",
        "lowest_line": "Lowest {name}: {label} ({value}).",
        "need_two": "Please name two months to compare, for example: \"Compare prices of March and June 2026\".",
        "compare_missing": "I have no records for: {months}. I cannot compare without them.",
        "compare_line": "The {name} in {b_label} is {direction} than in {a_label}: {b_val} vs {a_val} (difference {diff}, {pct}).",
        "compare_same": "The {name} is the same in {a_label} and {b_label}: {a_val}.",
        "up": "higher", "down": "lower",
        "need_trend": "I need at least 2 months of records in that range to show a trend.",
        "trend_up": "From {first} to {last}, the {name} went up by {diff} ({pct}).",
        "trend_down": "From {first} to {last}, the {name} went down by {diff} ({pct}).",
        "trend_flat": "From {first} to {last}, the {name} stayed the same.",
        "price_note": "Prices are averages weighted by kilos.",
        "gap_note": "No records for these months (not filled in): {months}.",
    },
    "fil": {
        "greeting": "Kumusta! Ako si BakaTrack. Magtanong ka tungkol sa kilo, bilang ng baka at presyo mula sa datos ng tab na ito.",
        "goodbye": "Paalam! Mangyaring kumpirmahin sa tanggapan ng palengke ang mahahalagang desisyon.",
        "help": "Maaari mong itanong: kabuuang kilo, bilang ng baka, pinakamataas o pinakamababang buwan, paghahambing ng presyo ng dalawang buwan, at takbo ng presyo. Halimbawa: \"Ipakita ang presyo mula Enero hanggang Hunyo 2026\".",
        "upload_help": "Para magdagdag ng datos, pindutin ang + at mag-upload ng CSV na may mga column na: date (YYYY-MM-DD), head_count, total_kilos, price_per_kilo. Kung may mali, sasabihin ko at walang masesave.",
        "out_of_scope": "Pasensya na, ang masasagot ko lang ay tungkol sa dami at presyo ng baka mula sa datos na naka-load.",
        "referral": "Hindi ako sigurado kung naintindihan ko iyon (kumpiyansa {conf}%). Pakisabi ulit sa ibang paraan, o magtanong sa pamunuan ng palengke o sa Municipal Agriculture Office.",
        "no_data": "Walang talaan mula {start} hanggang {end} sa tab na ito, kaya hindi ako makasasagot. Subukan ang ibang petsa.",
        "empty_dataset": "Wala pang talaan ang tab na ito. Mag-upload ng CSV gamit ang + button.",
        "empty_message": "Mag-type po ng tanong.",
        "error": "Pasensya na, may problema sa panig ko. Subukan ulit.",
        "coming": "Hindi pa available ang feature na ito sa bersyong ito.",
        "range_line": "Saklaw: {start} hanggang {end}, {n} buwan ng talaan ang ginamit.",
        "total_line": "{name}: {value}",
        "peak_line": "Pinakamataas na {name}: {label} ({value}).",
        "lowest_line": "Pinakamababang {name}: {label} ({value}).",
        "need_two": "Pakisabi ang dalawang buwan na ihahambing, halimbawa: \"Ihambing ang presyo ng Marso at Hunyo 2026\".",
        "compare_missing": "Walang talaan para sa: {months}. Hindi ako makapaghahambing kung wala ito.",
        "compare_line": "Ang {name} sa {b_label} ay {direction} kaysa sa {a_label}: {b_val} laban sa {a_val} (pagkakaiba {diff}, {pct}).",
        "compare_same": "Pareho ang {name} sa {a_label} at {b_label}: {a_val}.",
        "up": "mas mataas", "down": "mas mababa",
        "need_trend": "Kailangan ko ng hindi bababa sa 2 buwan ng talaan sa saklaw na iyon para ipakita ang takbo.",
        "trend_up": "Mula {first} hanggang {last}, tumaas ang {name} ng {diff} ({pct}).",
        "trend_down": "Mula {first} hanggang {last}, bumaba ang {name} ng {diff} ({pct}).",
        "trend_flat": "Mula {first} hanggang {last}, hindi nagbago ang {name}.",
        "price_note": "Ang presyo ay average na may timbang batay sa kilo.",
        "gap_note": "Walang talaan para sa mga buwang ito (hindi pinunan): {months}.",
    },
}

METRIC_NAME = {
    "en": {"total_kilos": "total kilos", "head_count": "head count", "price_per_kilo": "price per kilo"},
    "fil": {"total_kilos": "kabuuang kilo", "head_count": "bilang ng ulo", "price_per_kilo": "presyo kada kilo"},
}


def t(lang, key, **values):
    """Pick a template in the chosen language and fill in the values."""
    return TEXT[lang][key].format(**values)


def fmt_value(metric, value):
    if metric == "price_per_kilo":
        return "₱{:,.2f}".format(value)
    if metric == "head_count":
        return "{:,}".format(int(value))
    return "{:,.0f} kg".format(value)


def fmt_percent(percent):
    return "n/a" if percent is None else "{:.1f}%".format(abs(percent))


def _footer(lang, parsed, summary, metric):
    """Honesty lines: assumptions the parser made, price method, missing months."""
    lines = list(parsed.get("notes", []))
    if metric == "price_per_kilo":
        lines.append(t(lang, "price_note"))
    if summary["gaps"]:
        lines.append(t(lang, "gap_note", months=", ".join(summary["gaps"])))
    return lines


def _compare(lang, parsed, summary, metric, name):
    months = parsed.get("months") or []
    if len(months) < 2:
        return [t(lang, "need_two")]
    result = qe.compare_months(summary, months[0], months[-1], metric)
    if not result["found"]:
        return [t(lang, "compare_missing", months=", ".join(result["missing"]))]
    a, b = result["a"], result["b"]
    values = dict(name=name, a_label=a["label"], b_label=b["label"],
                  a_val=fmt_value(metric, a[metric]), b_val=fmt_value(metric, b[metric]))
    if result["difference"] == 0:
        return [t(lang, "compare_same", **values)]
    direction = t(lang, "up") if result["difference"] > 0 else t(lang, "down")
    return [t(lang, "compare_line", direction=direction,
              diff=fmt_value(metric, abs(result["difference"])),
              pct=fmt_percent(result["percent"]), **values)]


def _trend(lang, summary, metric, name):
    months = summary["months"]
    if len(months) < 2:
        return [t(lang, "need_trend")]
    lines = [m["label"] + ": " + fmt_value(metric, m[metric]) for m in months]
    first, last = months[0], months[-1]
    diff = round(last[metric] - first[metric], 2)
    percent = round(diff / first[metric] * 100, 1) if first[metric] else None
    key = "trend_flat" if diff == 0 else ("trend_up" if diff > 0 else "trend_down")
    lines.append(t(lang, key, first=first["label"], last=last["label"], name=name,
                   diff=fmt_value(metric, abs(diff)), pct=fmt_percent(percent)))
    return lines


def build_answer(intent, lang, parsed, summary):
    """Turn real numbers into a written answer. Returns plain text."""
    if intent == "total_kilos":
        metric = "total_kilos"
    elif intent == "head_count":
        metric = "head_count"
    else:
        metric = parsed["metric"]
    name = METRIC_NAME[lang][metric]
    lines = [t(lang, "range_line", start=summary["start"], end=summary["end"],
               n=summary["months_used"])]

    if intent in ("total_kilos", "head_count"):
        lines.append(t(lang, "total_line", name=name.capitalize(),
                       value=fmt_value(metric, qe.total_of(summary, metric))))
    elif intent == "peak_month":
        m = qe.peak_month(summary, metric)
        lines.append(t(lang, "peak_line", name=name, label=m["label"], value=fmt_value(metric, m[metric])))
    elif intent == "lowest_month":
        m = qe.lowest_month(summary, metric)
        lines.append(t(lang, "lowest_line", name=name, label=m["label"], value=fmt_value(metric, m[metric])))
    elif intent == "price_compare":
        metric = parsed["metric"]
        lines += _compare(lang, parsed, summary, metric, METRIC_NAME[lang][metric])
    elif intent == "price_trend":
        lines += _trend(lang, summary, metric, name)

    return "\n".join(lines + _footer(lang, parsed, summary, metric))


TEXT["en"].update({
    "rate_main_above": "The average price in {label} is \u20b1{price} per kilo, {pct}% above the overall average of \u20b1{hist}.",
    "rate_main_below": "The average price in {label} is \u20b1{price} per kilo, {pct}% below the overall average of \u20b1{hist}.",
    "rate_main_same": "The average price in {label} is \u20b1{price} per kilo, about the same as the overall average of \u20b1{hist}.",
    "rate_result": "Price rating: {rating} (fuzzy score {score}/100). {advice}",
    "rating_low": "Low", "rating_normal": "Normal", "rating_high": "High",
    "advice_low": "Buyers have the advantage.",
    "advice_normal": "The market looks stable.",
    "advice_high": "Sellers have the advantage.",
    "rate_footer": "Based on {n} months of records ({first} to {last}), prices weighted by kilos. Membership: Low {low}, Normal {normal}, High {high}. Guide only, not a guarantee.",
    "rate_need_more": "I need at least {min} months of records to rate a price, and this dataset has {n}.",
    "rate_no_month": "There are no records for {label}, so I cannot rate it.",
})
TEXT["fil"].update({
    "rate_main_above": "Ang average na presyo noong {label} ay \u20b1{price} kada kilo, {pct}% na mas mataas kaysa sa kabuuang average na \u20b1{hist}.",
    "rate_main_below": "Ang average na presyo noong {label} ay \u20b1{price} kada kilo, {pct}% na mas mababa kaysa sa kabuuang average na \u20b1{hist}.",
    "rate_main_same": "Ang average na presyo noong {label} ay \u20b1{price} kada kilo, halos pareho sa kabuuang average na \u20b1{hist}.",
    "rate_result": "Antas ng presyo: {rating} (fuzzy score {score}/100). {advice}",
    "rating_low": "Mababa", "rating_normal": "Normal", "rating_high": "Mataas",
    "advice_low": "Mas may kalamangan ang mga mamimili.",
    "advice_normal": "Mukhang matatag ang merkado.",
    "advice_high": "Mas may kalamangan ang mga nagbebenta.",
    "rate_footer": "Batay sa {n} buwan ng talaan ({first} hanggang {last}), presyong may timbang batay sa kilo. Membership: Low {low}, Normal {normal}, High {high}. Gabay lamang, hindi garantiya.",
    "rate_need_more": "Kailangan ko ng hindi bababa sa {min} buwan ng talaan para mag-rate ng presyo, at {n} lang ang meron ang dataset na ito.",
    "rate_no_month": "Walang talaan para sa {label}, kaya hindi ko ito ma-rate.",
})
