import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = BASE_DIR / "dataset" / "processed" / "sales_product_master_imputed.csv"

CHUNK_SIZE = 500_000

print("Starting chunk-wise demand analysis...")

# product_id -> daily quantity
daily_demand = {}

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

    chunk["date_"] = pd.to_datetime(
        chunk["date_"],
        errors="coerce"
    )

    # Daily demand
    daily = (
        chunk.groupby(
            ["date_", "product_id"]
        )["procured_quantity"]
        .sum()
        .reset_index()
    )

    # Store daily demand
    for row in daily.itertuples(index=False):
        key = row.product_id

        if key not in daily_demand:
            daily_demand[key] = {}

        daily_demand[key][row.date_] = (
            daily_demand[key].get(row.date_, 0)
            + row.procured_quantity
        )

    if chunk_no % 5 == 0:
        print(f"Processed rows: {total_rows:,}")


print("\n========== BUILDING VOLATILITY METRICS ==========")

results = []

for product_id, values in daily_demand.items():

    demand = pd.Series(values).sort_index()

    # Full date range
    full_dates = pd.date_range(
        demand.index.min(),
        demand.index.max(),
        freq="D"
    )

    demand = demand.reindex(
        full_dates,
        fill_value=0
    )

    avg_demand = demand.mean()
    std_demand = demand.std()

    if avg_demand > 0:
        cv = std_demand / avg_demand
    else:
        cv = 0

    zero_days = (demand == 0).sum()
    active_days = (demand > 0).sum()

    results.append(
        {
            "product_id": product_id,
            "avg_daily_demand": avg_demand,
            "std_daily_demand": std_demand,
            "cv": cv,
            "zero_demand_days": zero_days,
            "active_demand_days": active_days,
            "total_demand": demand.sum()
        }
    )


volatility = pd.DataFrame(results)

print("\nTotal products analyzed:", len(volatility))

# ------------------------------------------------
# VOLATILITY CLASSIFICATION
# ------------------------------------------------

def classify_cv(cv):

    if cv < 0.5:
        return "Low"

    elif cv < 1.0:
        return "Medium"

    else:
        return "High"


volatility["volatility_class"] = (
    volatility["cv"].apply(classify_cv)
)


# ------------------------------------------------
# SUMMARY
# ------------------------------------------------

print("\n========== VOLATILITY SUMMARY ==========")

summary = (
    volatility
    .groupby("volatility_class")
    .agg(
        products=("product_id", "count"),
        avg_demand=("avg_daily_demand", "mean"),
        avg_cv=("cv", "mean")
    )
)

print(summary)


# ------------------------------------------------
# MOST VOLATILE PRODUCTS
# ------------------------------------------------

print("\n========== TOP 20 MOST VOLATILE PRODUCTS ==========")

top_volatile = (
    volatility
    .sort_values("cv", ascending=False)
    .head(20)
)

print(top_volatile.to_string(index=False))


# ------------------------------------------------
# HIGHEST DEMAND PRODUCTS
# ------------------------------------------------

print("\n========== TOP 20 PRODUCTS BY AVERAGE DAILY DEMAND ==========")

top_demand = (
    volatility
    .sort_values(
        "avg_daily_demand",
        ascending=False
    )
    .head(20)
)

print(top_demand.to_string(index=False))


# ------------------------------------------------
# ZERO DEMAND
# ------------------------------------------------

print("\n========== ZERO DEMAND ANALYSIS ==========")

print(
    "Products with at least one zero-demand day:",
    (volatility["zero_demand_days"] > 0).sum()
)

print(
    "Products with more than 50% zero-demand days:",
    (
        volatility["zero_demand_days"]
        /
        (
            volatility["zero_demand_days"]
            +
            volatility["active_demand_days"]
        )
        > 0.5
    ).sum()
)


# ------------------------------------------------
# AVERAGE DEMAND + VOLATILITY
# ------------------------------------------------

print("\n========== HIGH DEMAND + HIGH VOLATILITY ==========")

high_demand_threshold = volatility["avg_daily_demand"].quantile(0.75)
high_cv_threshold = volatility["cv"].quantile(0.75)

high_priority = volatility[
    (volatility["avg_daily_demand"] >= high_demand_threshold)
    &
    (volatility["cv"] >= high_cv_threshold)
]

print(
    "Products:",
    len(high_priority)
)

print(
    high_priority
    .sort_values(
        ["avg_daily_demand", "cv"],
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)


print("\n========== DONE ==========")