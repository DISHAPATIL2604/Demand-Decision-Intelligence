import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILE = BASE_DIR / "dataset" / "processed" / "sales_product_master_imputed.csv"

CHUNK_SIZE = 500_000

print("Starting demand segmentation...")

# ------------------------------------------------
# STEP 1: Aggregate product-level daily demand
# ------------------------------------------------

product_daily = {}

total_rows = 0

for chunk_no, chunk in enumerate(
    pd.read_csv(
        FILE,
        usecols=["date_", "product_id", "procured_quantity"],
        chunksize=CHUNK_SIZE
    ),
    start=1
):
    total_rows += len(chunk)

    chunk["date_"] = pd.to_datetime(chunk["date_"], errors="coerce")

    daily = (
        chunk.groupby(["date_", "product_id"])["procured_quantity"]
        .sum()
        .reset_index()
    )

    for row in daily.itertuples(index=False):
        product_id = row.product_id
        date = row.date_

        if product_id not in product_daily:
            product_daily[product_id] = {}

        product_daily[product_id][date] = (
            product_daily[product_id].get(date, 0)
            + row.procured_quantity
        )

    if chunk_no % 5 == 0:
        print(f"Processed rows: {total_rows:,}")


print("\n========== CALCULATING PRODUCT METRICS ==========")

results = []

# Entire dataset period
all_dates = pd.date_range(
    "2022-04-01",
    "2022-07-10",
    freq="D"
)

for product_id, values in product_daily.items():

    demand = pd.Series(values)

    # Force every product onto the same 101-day period
    demand = demand.reindex(all_dates, fill_value=0)

    total_demand = demand.sum()
    avg_daily_demand = demand.mean()
    std_daily_demand = demand.std()

    if avg_daily_demand > 0:
        cv = std_daily_demand / avg_daily_demand
    else:
        cv = 0

    active_days = (demand > 0).sum()
    zero_days = (demand == 0).sum()

    demand_day_ratio = active_days / len(all_dates)

    results.append({
        "product_id": product_id,
        "total_demand": total_demand,
        "avg_daily_demand": avg_daily_demand,
        "std_daily_demand": std_daily_demand,
        "cv": cv,
        "active_days": active_days,
        "zero_days": zero_days,
        "demand_day_ratio": demand_day_ratio
    })


df = pd.DataFrame(results)


# ------------------------------------------------
# STEP 2: Demand volume classification
# ------------------------------------------------

print("\n========== DEMAND VOLUME CLASSIFICATION ==========")

volume_50 = df["avg_daily_demand"].median()
volume_75 = df["avg_daily_demand"].quantile(0.75)

def classify_volume(x):

    if x >= volume_75:
        return "High"

    elif x >= volume_50:
        return "Medium"

    else:
        return "Low"


df["demand_volume"] = df["avg_daily_demand"].apply(classify_volume)


# ------------------------------------------------
# STEP 3: Volatility classification
# ------------------------------------------------

def classify_volatility(cv):

    if cv < 0.5:
        return "Stable"

    elif cv < 1.0:
        return "Moderate"

    else:
        return "Volatile"


df["volatility"] = df["cv"].apply(classify_volatility)


# ------------------------------------------------
# STEP 4: Intermittent demand
# ------------------------------------------------

def classify_intermittency(ratio):

    if ratio < 0.25:
        return "Highly Intermittent"

    elif ratio < 0.50:
        return "Intermittent"

    else:
        return "Regular"


df["demand_pattern"] = (
    df["demand_day_ratio"]
    .apply(classify_intermittency)
)


# ------------------------------------------------
# STEP 5: ABC classification
# ------------------------------------------------

df = df.sort_values(
    "total_demand",
    ascending=False
).reset_index(drop=True)

df["demand_share_%"] = (
    df["total_demand"]
    / df["total_demand"].sum()
    * 100
)

df["cumulative_demand_%"] = (
    df["demand_share_%"].cumsum()
)

def classify_abc(x):

    if x <= 80:
        return "A"

    elif x <= 95:
        return "B"

    else:
        return "C"


df["ABC_class"] = (
    df["cumulative_demand_%"]
    .apply(classify_abc)
)


# ------------------------------------------------
# STEP 6: Combined segment
# ------------------------------------------------

df["segment"] = (
    df["ABC_class"]
    + " | "
    + df["demand_volume"]
    + " | "
    + df["volatility"]
    + " | "
    + df["demand_pattern"]
)


# ------------------------------------------------
# SUMMARY
# ------------------------------------------------

print("\n========== DEMAND VOLUME SUMMARY ==========")

print(
    df["demand_volume"]
    .value_counts()
)


print("\n========== VOLATILITY SUMMARY ==========")

print(
    df["volatility"]
    .value_counts()
)


print("\n========== DEMAND PATTERN SUMMARY ==========")

print(
    df["demand_pattern"]
    .value_counts()
)


print("\n========== ABC SUMMARY ==========")

abc = (
    df.groupby("ABC_class")
    .agg(
        products=("product_id", "count"),
        total_demand=("total_demand", "sum")
    )
)

abc["demand_share_%"] = (
    abc["total_demand"]
    / df["total_demand"].sum()
    * 100
)

print(abc)


# ------------------------------------------------
# MOST IMPORTANT SEGMENTS
# ------------------------------------------------

print("\n========== SEGMENT SUMMARY ==========")

segment_summary = (
    df.groupby("segment")
    .agg(
        products=("product_id", "count"),
        total_demand=("total_demand", "sum"),
        avg_daily_demand=("avg_daily_demand", "mean")
    )
    .sort_values("total_demand", ascending=False)
)

print(segment_summary.head(20))


# ------------------------------------------------
# HIGH PRIORITY PRODUCTS
# ------------------------------------------------

print("\n========== HIGH PRIORITY PRODUCTS ==========")

high_priority = df[
    (df["ABC_class"] == "A")
    &
    (df["demand_volume"] == "High")
    &
    (df["volatility"].isin(["Moderate", "Volatile"]))
]

print(
    "High-priority products:",
    len(high_priority)
)

print(
    high_priority[
        [
            "product_id",
            "total_demand",
            "avg_daily_demand",
            "cv",
            "active_days",
            "ABC_class",
            "demand_volume",
            "volatility",
            "demand_pattern"
        ]
    ]
    .sort_values("total_demand", ascending=False)
    .head(20)
    .to_string(index=False)
)


# ------------------------------------------------
# SLOW MOVING PRODUCTS
# ------------------------------------------------

print("\n========== SLOW / INTERMITTENT PRODUCTS ==========")

slow = df[
    (df["demand_pattern"].isin(
        ["Intermittent", "Highly Intermittent"]
    ))
]

print(
    "Slow/intermittent products:",
    len(slow)
)

print(
    "Share of products:",
    round(len(slow) / len(df) * 100, 2),
    "%"
)


# ------------------------------------------------
# FINAL
# ------------------------------------------------

print("\n========== FINAL SEGMENTATION ==========")

print(
    df[
        [
            "ABC_class",
            "demand_volume",
            "volatility",
            "demand_pattern"
        ]
    ]
    .value_counts()
    .head(20)
)


print("\n========== DONE ==========")