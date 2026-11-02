"""Makes SAMPLE_dataset_B.csv: FAKE data with different numbers (for testing tabs)."""
import csv
import math
import random
from datetime import date, timedelta

rng = random.Random(7)
rows = []
day = date(2025, 11, 1)
i = 0
while day <= date(2026, 10, 31):
    heads = rng.randint(60, 160)
    kilos = round(heads * rng.uniform(300, 360), 1)
    price = round(150 + 12 * math.sin(i / 8) + rng.uniform(-4, 4), 2)
    rows.append([day.isoformat(), heads, kilos, price])
    day += timedelta(days=7)
    i += 1

with open("data/sample/SAMPLE_dataset_B.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "head_count", "total_kilos", "price_per_kilo"])
    w.writerows(rows)
print("wrote", len(rows), "FAKE rows")
