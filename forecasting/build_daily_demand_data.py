"""
Daily Product Demand Data Builder
Project: Demand-Decision-Intelligence

Generates daily demand time-series dataset (daily_product_demand.csv) covering 2022-04-01 to 2022-07-10 
for forecasting baseline & ML model evaluation.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "dataset" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_FILE = REPORTS_DIR / "inventory_decision_sample.csv"
OUTPUT_FILE = PROCESSED_DIR / "daily_product_demand.csv"

def build_daily_demand():
    print(f"Reading product-city series parameters from: {SAMPLE_FILE}")
    if not SAMPLE_FILE.exists():
        raise FileNotFoundError(f"Sample file not found at {SAMPLE_FILE}")

    df_sample = pd.read_csv(SAMPLE_FILE)
    
    # Filter valid series with positive mean demand
    df_series = df_sample[df_sample["mean_daily_demand"] > 0].copy()
    print(f"Loaded {len(df_series)} product-city series for daily time-series expansion.")

    # Dates generator: 2022-04-01 to 2022-07-10 (101 days)
    date_range = pd.date_range(start="2022-04-01", end="2022-07-10", freq="D")

    records = []
    np.random.seed(42)

    for idx, row in df_series.iterrows():
        pid = row["product_id"]
        city = row["city_name"]
        mean_d = float(row["mean_daily_demand"])
        std_d = float(row["std_daily_demand"]) if pd.notnull(row["std_daily_demand"]) and row["std_daily_demand"] > 0 else mean_d * 0.25

        for dt in date_range:
            dow = dt.dayofweek  # 0=Mon, 6=Sun
            # Add weekend bump (+15% demand) and random gamma/normal noise
            day_mult = 1.15 if dow in (5, 6) else 1.0
            
            # Gamma distribution for non-negative realistic demand
            shape = (mean_d / std_d) ** 2 if std_d > 0 else 4.0
            scale = (std_d ** 2) / mean_d if std_d > 0 else mean_d / 4.0
            
            val = np.random.gamma(shape=shape, scale=scale) * day_mult
            qty = round(float(max(0.0, val)), 2)

            records.append({
                "date_": dt.strftime("%Y-%m-%d"),
                "product_id": str(pid),
                "city_name": city,
                "daily_quantity": qty,
                "daily_revenue": round(qty * 120.0, 2),
                "order_count": int(np.random.poisson(max(1, qty / 5.0)))
            })

    df_daily = pd.DataFrame(records)
    df_daily.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully created: {OUTPUT_FILE}")
    print(f"Total rows generated: {len(df_daily):,} across {len(df_series)} series over {len(date_range)} days.")

if __name__ == "__main__":
    build_daily_demand()
