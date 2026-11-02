# Creates a SAMPLE dataset for development ONLY. These numbers are made up, NOT real market data.
import os
import numpy as np
import pandas as pd

np.random.seed(42)
dates = pd.date_range("2025-11-01", "2026-10-31", freq="7D")   # one auction per week

df = pd.DataFrame({
    "date": dates.strftime("%Y-%m-%d"),
    "head_count": np.random.randint(80, 220, len(dates)),
    "total_kilos": np.random.randint(18000, 52000, len(dates)),
    "price_per_kilo": np.round(np.random.uniform(105, 145, len(dates)), 2),
})

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SAMPLE_cattle_data.csv")
df.to_csv(out, index=False)
print("Saved SAMPLE file:", out, "| rows:", len(df))
