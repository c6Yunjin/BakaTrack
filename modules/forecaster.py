"""Forecaster (Step 9). Two simple methods written by hand, no AI model.

1) average : mean of the last 3 months
2) trend   : a straight line through all months (least squares, NumPy)
For each value we TEST both methods on the last 3 known months (backtest),
measure the error (MAPE and MAE), and use the method with the smaller error.
"""
import numpy as np

from modules import query_engine as qe
from modules import response_builder as rb

MIN_MONTHS = 6      # less history than this -> we do not forecast
HOLD_OUT = 3        # the last 3 months are used to test the methods
METRICS = ["price_per_kilo", "total_kilos", "head_count"]


def next_month(year, month):
    """The calendar month after (year, month)."""
    return (year + 1, 1) if month == 12 else (year, month + 1)


def _month_number(m):
    return m["year"] * 12 + m["month"] - 1


def predict_average(xs, ys, next_x):
    """Average of the last 3 months."""
    return float(np.mean(ys[-3:]))


def predict_trend(xs, ys, next_x):
    """Straight line through the points, extended one month ahead."""
    slope, intercept = np.polyfit(xs, ys, 1)
    return float(slope * next_x + intercept)


METHODS = {"average": predict_average, "trend": predict_trend}


def backtest(xs, ys, predict):
    """Predict each of the last 3 months from the months before it. Returns (MAPE %, MAE)."""
    errors, percents = [], []
    for i in range(len(ys) - HOLD_OUT, len(ys)):
        guess = predict(xs[:i], ys[:i], xs[i])
        errors.append(abs(ys[i] - guess))
        if ys[i] != 0:
            percents.append(abs(ys[i] - guess) / abs(ys[i]) * 100)
    mape = float(np.mean(percents)) if percents else None
    return mape, float(np.mean(errors))


def forecast_metric(months, metric):
    """Forecast ONE value (price, kilos or heads) for the month after the last one."""
    first = _month_number(months[0])
    xs = [_month_number(m) - first for m in months]
    ys = [m[metric] for m in months]
    next_x = xs[-1] + 1
    scores = {}
    for name, predict in METHODS.items():
        mape, mae = backtest(xs, ys, predict)
        scores[name] = (mape, mae)
    # trend must be strictly better to win, so ties go to the simpler average
    def score(name):
        return scores[name][0] if scores[name][0] is not None else float("inf")
    best = "trend" if score("trend") < score("average") else "average"
    value = max(0.0, METHODS[best](xs, ys, next_x))
    return {"metric": metric, "value": value, "method": best,
            "mape": scores[best][0], "mae": scores[best][1]}


def forecast_answer(dataset_id, lang):
    """Forecast next month for ONE dataset, using only that dataset's months."""
    summary = qe.get_summary(dataset_id, None, None)
    months = summary["months"]
    if len(months) < MIN_MONTHS:
        return rb.t(lang, "fc_need_more", min=MIN_MONTHS, n=len(months))

    results = {metric: forecast_metric(months, metric) for metric in METRICS}
    year, month = next_month(months[-1]["year"], months[-1]["month"])
    label = qe.MONTH_NAMES[month - 1] + " " + str(year)

    main = rb.t(lang, "fc_main", label=label,
                price=rb.fmt_value("price_per_kilo", results["price_per_kilo"]["value"]),
                kilos=rb.fmt_value("total_kilos", results["total_kilos"]["value"]),
                heads=rb.fmt_value("head_count", results["head_count"]["value"]))
    items = []
    for metric in METRICS:
        r = results[metric]
        error = "n/a" if r["mape"] is None else "{:.1f}%".format(r["mape"])
        items.append(rb.t(lang, "fc_item", name=rb.METRIC_NAME[lang][metric],
                          method=rb.t(lang, "fc_method_" + r["method"]), error=error))
    how = rb.t(lang, "fc_how", k=HOLD_OUT, detail="; ".join(items))
    footer = rb.t(lang, "fc_footer", n=len(months), first=months[0]["label"],
                  last=months[-1]["label"])
    lines = [main, how, footer]
    if summary["gaps"]:
        lines.append(rb.t(lang, "gap_note", months=", ".join(summary["gaps"])))
    return "\n".join(lines)
