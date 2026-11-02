"""Chart maker (Step 7).

Turns the monthly numbers from the query engine into chart data (labels + values)
and a short written summary. The browser draws it with Chart.js.
A month with no records gets an empty value (a gap in the chart), never an invented number.
"""
import re

from modules import query_engine as qe
from modules import response_builder as rb

CHART_LINE = {"en": "Chart: {name} per month.", "fil": "Tsart: {name} kada buwan.",
              "taglish": "Chart: {name} kada buwan."}


def chart_type_for(metric, message=""):
    """Price -> line, kilos/heads -> bar. The words 'bar' or 'line' in the question win."""
    words = re.findall(r"[a-z]+", str(message).lower())
    if "bar" in words:
        return "bar"
    if "line" in words:
        return "line"
    return "line" if metric == "price_per_kilo" else "bar"


def _month_range(months):
    """Every (year, month) from the first to the last month with records."""
    y, m = months[0]["year"], months[0]["month"]
    last = (months[-1]["year"], months[-1]["month"])
    out = []
    while (y, m) <= last:
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def build_chart(summary, metric, chart_type, lang):
    """Chart data for the page: one label and one value per month."""
    by_month = {(m["year"], m["month"]): m for m in summary["months"]}
    labels, values = [], []
    for year, month in _month_range(summary["months"]):
        labels.append(qe.MONTH_NAMES[month - 1][:3] + " " + str(year))
        row = by_month.get((year, month))
        values.append(row[metric] if row else None)
    return {"type": chart_type, "labels": labels, "values": values,
            "metric": metric, "label": rb.METRIC_NAME[lang][metric]}


def build_chart_answer(lang, parsed, summary, message):
    """Short written summary + chart data. Returns (text, chart)."""
    metric = parsed["metric"]
    name = rb.METRIC_NAME[lang][metric]
    lines = [CHART_LINE[lang].format(name=name)]
    if summary["months_used"] >= 2:
        top, low = qe.peak_month(summary, metric), qe.lowest_month(summary, metric)
        lines.append(rb.t(lang, "peak_line", name=name, label=top["label"],
                          value=rb.fmt_value(metric, top[metric])))
        lines.append(rb.t(lang, "lowest_line", name=name, label=low["label"],
                          value=rb.fmt_value(metric, low[metric])))
    chart = build_chart(summary, metric, chart_type_for(metric, message), lang)
    text = "\n".join(lines) + "\n\n" + rb._footer_line(lang, parsed, summary, metric)
    return text, chart
