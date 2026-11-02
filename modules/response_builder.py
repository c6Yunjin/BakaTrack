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
    lines = _translated_notes(lang, parsed)
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
    lines = []

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

    return "\n".join(lines) + "\n\n" + _footer_line(lang, parsed, summary, metric)


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


TEXT["en"].update({
    "fc_main": "Forecast for {label}: price about {price} per kilo, total about {kilos}, head count about {heads}.",
    "fc_how": "Each value uses the simple method (average of the last 3 months, or trend line) that had the smaller error when tested on the last {k} known months. {detail}.",
    "fc_item": "{name}: {method}, error {error}",
    "fc_method_average": "average of last 3 months",
    "fc_method_trend": "trend line",
    "fc_footer": "Based on {n} months of records ({first} to {last}). This is an estimate, a guide only and not a guarantee. No seasonal pattern is claimed.",
    "fc_need_more": "I need at least {min} months of records to make a forecast, and this dataset has {n}.",
})
TEXT["fil"].update({
    "fc_main": "Pagtataya para sa {label}: presyo na humigit-kumulang {price} kada kilo, kabuuang humigit-kumulang {kilos}, at bilang ng ulo na humigit-kumulang {heads}.",
    "fc_how": "Ang bawat halaga ay gumagamit ng simpleng paraan (average ng huling 3 buwan, o linya ng takbo) na mas maliit ang error nang subukan sa huling {k} buwan. {detail}.",
    "fc_item": "{name}: {method}, error {error}",
    "fc_method_average": "average ng huling 3 buwan",
    "fc_method_trend": "linya ng takbo",
    "fc_footer": "Batay sa {n} buwan ng talaan ({first} hanggang {last}). Pagtataya lamang ito, gabay at hindi garantiya. Walang inaangking pana-panahong pattern.",
    "fc_need_more": "Kailangan ko ng hindi bababa sa {min} buwan ng talaan para magtaya, at {n} lang ang meron ang dataset na ito.",
})


TEXT["en"].update({
    "footer_many": "Period: {first} to {last} ({n} months of records used).",
    "footer_one": "Period: {label} (1 month of records used).",
})
TEXT["fil"].update({
    "footer_many": "Saklaw: {first} hanggang {last} ({n} buwan ng talaan ang ginamit).",
    "footer_one": "Saklaw: {label} (1 buwan ng talaan ang ginamit).",
})


def _footer_line(lang, parsed, summary, metric):
    """One small line under the answer: period, months used, notes."""
    months = summary["months"]
    first, last = months[0]["label"], months[-1]["label"]
    if first == last:
        period = t(lang, "footer_one", label=first)
    else:
        period = t(lang, "footer_many", first=first, last=last, n=summary["months_used"])
    return " ".join([period] + _footer(lang, parsed, summary, metric))


# ---------- Taglish (third reply language) ----------
TEXT["taglish"] = dict(TEXT["fil"])          # start from Filipino, then replace every line
TEXT["taglish"].update({
    "greeting": "Hi! Ako si BakaTrack. Tanungin mo ako tungkol sa kilos, head count at presyo ng baka mula sa data ng dataset na ito.",
    "goodbye": "Bye! Paki-confirm pa rin sa market office ang mahahalagang desisyon.",
    "help": "Pwede mong itanong: total kilos, head count, highest o lowest month, price comparison ng dalawang buwan, at price trend. Example: \"Show prices from January to June 2026\".",
    "upload_help": "Para mag-add ng data, i-click ang + at mag-upload ng CSV na may columns na: date (YYYY-MM-DD), head_count, total_kilos, price_per_kilo. Kapag may mali, sasabihin ko at walang masesave.",
    "out_of_scope": "Sorry, cattle volume at presyo lang ang masasagot ko mula sa loaded data.",
    "referral": "Hindi ako sure kung naintindihan ko (confidence {conf}%). Paki-rephrase, o magtanong sa market administration o sa Municipal Agriculture Office.",
    "no_data": "Walang records mula {start} hanggang {end} sa dataset na ito, kaya hindi ako makakasagot. Try mo ang ibang date range.",
    "empty_dataset": "Wala pang records ang dataset na ito. Mag-upload ng CSV gamit ang + button.",
    "empty_message": "Paki-type ang tanong mo.",
    "error": "Sorry, may problema sa side ko. Try mo ulit.",
    "coming": "Hindi pa available ang feature na ito sa version na ito.",
    "range_line": "Saklaw: {start} hanggang {end}, {n} buwan ng records ang ginamit.",
    "total_line": "{name}: {value}",
    "peak_line": "Pinakamataas na {name}: {label} ({value}).",
    "lowest_line": "Pinakamababang {name}: {label} ({value}).",
    "need_two": "Paki-sabi ang dalawang buwan na ico-compare, halimbawa: \"Compare prices of March and June 2026\".",
    "compare_missing": "Walang records para sa: {months}. Hindi ako makaka-compare kung wala ito.",
    "compare_line": "Mas {direction} ang {name} noong {b_label} kaysa noong {a_label}: {b_val} vs {a_val} (difference {diff}, {pct}).",
    "compare_same": "Pareho ang {name} noong {a_label} at {b_label}: {a_val}.",
    "up": "mataas", "down": "mababa",
    "need_trend": "Kailangan ko ng at least 2 buwan ng records sa range na iyon para ipakita ang trend.",
    "trend_up": "Mula {first} hanggang {last}, tumaas ang {name} ng {diff} ({pct}).",
    "trend_down": "Mula {first} hanggang {last}, bumaba ang {name} ng {diff} ({pct}).",
    "trend_flat": "Mula {first} hanggang {last}, hindi nagbago ang {name}.",
    "price_note": "Ang price ay average na weighted by kilos.",
    "gap_note": "Walang records para sa mga buwang ito (hindi pinunan): {months}.",
    "rate_main_above": "Ang average na price noong {label} ay \u20b1{price} per kilo, {pct}% na mas mataas kaysa sa overall average na \u20b1{hist}.",
    "rate_main_below": "Ang average na price noong {label} ay \u20b1{price} per kilo, {pct}% na mas mababa kaysa sa overall average na \u20b1{hist}.",
    "rate_main_same": "Ang average na price noong {label} ay \u20b1{price} per kilo, halos pareho sa overall average na \u20b1{hist}.",
    "rate_result": "Price rating: {rating} (fuzzy score {score}/100). {advice}",
    "rating_low": "Low", "rating_normal": "Normal", "rating_high": "High",
    "advice_low": "Mas may advantage ang mga buyer.",
    "advice_normal": "Mukhang stable ang market.",
    "advice_high": "Mas may advantage ang mga seller.",
    "rate_footer": "Batay sa {n} buwan ng records ({first} hanggang {last}), prices weighted by kilos. Membership: Low {low}, Normal {normal}, High {high}. Gabay lang, hindi garantiya.",
    "rate_need_more": "Kailangan ko ng at least {min} buwan ng records para mag-rate ng price, at {n} lang ang meron ang dataset na ito.",
    "rate_no_month": "Walang records para sa {label}, kaya hindi ko ito ma-rate.",
    "fc_main": "Forecast para sa {label}: price na mga {price} per kilo, total na mga {kilos}, at head count na mga {heads}.",
    "fc_how": "Ang bawat value ay gumagamit ng simpleng method (average ng last 3 months, o trend line) na mas maliit ang error nang i-test sa last {k} known months. {detail}.",
    "fc_item": "{name}: {method}, error {error}",
    "fc_method_average": "average ng last 3 months",
    "fc_method_trend": "trend line",
    "fc_footer": "Batay sa {n} buwan ng records ({first} hanggang {last}). Estimate lang ito, gabay at hindi garantiya. Walang seasonal pattern na inaangkin.",
    "fc_need_more": "Kailangan ko ng at least {min} buwan ng records para mag-forecast, at {n} lang ang meron ang dataset na ito.",
    "footer_many": "Period: {first} hanggang {last} ({n} buwan ng records ang ginamit).",
    "footer_one": "Period: {label} (1 buwan ng records ang ginamit).",
})
METRIC_NAME["taglish"] = {"total_kilos": "total kilos", "head_count": "head count",
                          "price_per_kilo": "price per kilo"}


# ---------- translated parser notes and month names ----------
import re

TEXT["en"].update({
    "note_relative": "Dates are counted from the latest record in the data ({latest}).",
    "note_swapped": "The dates were in reverse order, so I swapped them.",
    "note_default_range": "No dates were given, so I used the latest 6 months of data: {range}.",
    "note_no_metric": "No metric was given, so I assumed price.",
})
TEXT["fil"].update({
    "note_relative": "Ang mga petsa ay binibilang mula sa pinakabagong talaan sa datos ({latest}).",
    "note_swapped": "Magkabaligtad ang pagkakasunod ng mga petsa, kaya pinalitan ko ang ayos.",
    "note_default_range": "Walang binanggit na petsa, kaya ginamit ko ang pinakabagong 6 na buwan ng datos: {range}.",
    "note_no_metric": "Walang binanggit na sukatan, kaya ipinalagay kong presyo.",
})
TEXT["taglish"].update({
    "note_relative": "Ang dates ay binibilang mula sa latest record sa data ({latest}).",
    "note_swapped": "Baligtad ang order ng dates, kaya pinalitan ko.",
    "note_default_range": "Walang binanggit na petsa, kaya ginamit ko ang latest 6 months ng data: {range}.",
    "note_no_metric": "Walang binanggit na metric, kaya nag-assume ako ng price.",
})

FIL_MONTHS = {"January": "Enero", "February": "Pebrero", "March": "Marso", "April": "Abril",
              "May": "Mayo", "June": "Hunyo", "July": "Hulyo", "August": "Agosto",
              "September": "Setyembre", "October": "Oktubre", "November": "Nobyembre",
              "December": "Disyembre"}
_EN_MONTH = re.compile(r"\b(" + "|".join(FIL_MONTHS) + r")\b(?= \d)")   # only before a number


def localize_months(lang, text):
    """Filipino replies use Filipino month names. English and Taglish keep English names."""
    if lang != "fil":
        return text
    return _EN_MONTH.sub(lambda m: FIL_MONTHS[m.group(1)], text)


def _translated_notes(lang, parsed):
    """Parser notes written from our own templates in the reply language."""
    keys = parsed.get("note_keys")
    if keys is None:                       # older parser result: keep the English notes
        return [n for n in parsed.get("notes", []) if not n.startswith("Showing")]
    lines = []
    for key, values in keys:
        values = dict(values)
        if "range" in values and lang != "en":
            values["range"] = values["range"].replace(" to ", " hanggang ")
        lines.append(t(lang, "note_" + key, **values))
    return lines
