import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = BASE_DIR / "dataset" / "processed" / "daily_product_demand.csv"

print("Reading daily demand dataset...")

df = pd.read_csv(
    FILE,
    usecols=[
        "date_",
        "product_id",
        "city_name",
        "daily_quantity"
    ]
)

df["date_"] = pd.to_datetime(df["date_"])

print("\n========== ORIGINAL DATA ==========")
print("Rows:", len(df))
print("Start:", df["date_"].min())
print("End:", df["date_"].max())

# ------------------------------------------------
# CREATE COMPLETE CALENDAR
# ------------------------------------------------

print("\nCreating complete calendar...")

dates = pd.date_range(
    start="2022-04-01",
    end="2022-07-10",
    freq="D"
)

# Existing product-city combinations only
product_city = (
    df[["product_id", "city_name"]]
    .drop_duplicates()
)

print(
    "Product-city combinations:",
    len(product_city)
)

# Create calendar for every existing product-city combination
calendar = product_city.assign(key=1)

date_df = pd.DataFrame({
    "date_": dates,
    "key": 1
})

calendar = calendar.merge(
    date_df,
    on="key"
).drop(columns="key")

print(
    "Complete calendar rows:",
    len(calendar)
)

# ------------------------------------------------
# MERGE ACTUAL DEMAND
# ------------------------------------------------

print("\nMerging actual demand...")

calendar = calendar.merge(
    df,
    on=["date_", "product_id", "city_name"],
    how="left"
)

# No sale = zero demand
calendar["daily_quantity"] = (
    calendar["daily_quantity"]
    .fillna(0)
)

calendar = calendar.sort_values(
    ["product_id", "city_name", "date_"]
).reset_index(drop=True)

print(
    "Rows after calendar completion:",
    len(calendar)
)

# ------------------------------------------------
# TIME FEATURES
# ------------------------------------------------

calendar["day_of_week"] = (
    calendar["date_"].dt.dayofweek
)

calendar["is_weekend"] = (
    calendar["day_of_week"] >= 5
).astype(int)

group_cols = [
    "product_id",
    "city_name"
]

# ------------------------------------------------
# LAG FEATURES
# ------------------------------------------------

print("\nCreating lag features...")

group = calendar.groupby(
    group_cols
)["daily_quantity"]

calendar["lag_1"] = group.shift(1)
calendar["lag_7"] = group.shift(7)
calendar["lag_14"] = group.shift(14)
calendar["lag_28"] = group.shift(28)

# ------------------------------------------------
# ROLLING FEATURES
# ------------------------------------------------

print("Creating rolling features...")

calendar["rolling_mean_7"] = (
    calendar.groupby(group_cols)["daily_quantity"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .mean()
    )
)

calendar["rolling_mean_14"] = (
    calendar.groupby(group_cols)["daily_quantity"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(14)
        .mean()
    )
)

calendar["rolling_mean_28"] = (
    calendar.groupby(group_cols)["daily_quantity"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(28)
        .mean()
    )
)

calendar["rolling_std_7"] = (
    calendar.groupby(group_cols)["daily_quantity"]
    .transform(
        lambda x:
        x.shift(1)
        .rolling(7)
        .std()
    )
)

# ------------------------------------------------
# MODEL DATA
# ------------------------------------------------

feature_columns = [
    "date_",
    "product_id",
    "city_name",
    "daily_quantity",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_mean_14",
    "rolling_mean_28",
    "rolling_std_7",
    "day_of_week",
    "is_weekend"
]

model_df = calendar.dropna(
    subset=[
        "lag_1",
        "lag_7",
        "lag_14",
        "lag_28",
        "rolling_mean_7",
        "rolling_mean_14",
        "rolling_mean_28",
        "rolling_std_7"
    ]
)

# ------------------------------------------------
# VALIDATION
# ------------------------------------------------

print("\n========== CALENDAR VALIDATION ==========")

print(
    "Expected dates:",
    len(dates)
)

print(
    "Expected product-city combinations:",
    len(product_city)
)

print(
    "Expected maximum rows:",
    len(dates) * len(product_city)
)

print(
    "Actual calendar rows:",
    len(calendar)
)

print(
    "Missing demand values:",
    calendar["daily_quantity"].isna().sum()
)

print(
    "Zero-demand rows:",
    (calendar["daily_quantity"] == 0).sum()
)

# ------------------------------------------------
# FEATURE INFORMATION
# ------------------------------------------------

print("\n========== FEATURE INFORMATION ==========")

print(
    "Model rows:",
    len(model_df)
)

print(
    "Model start:",
    model_df["date_"].min()
)

print(
    "Model end:",
    model_df["date_"].max()
)

print("\nMissing feature values:")

print(
    model_df[feature_columns]
    .isna()
    .sum()
)

# ------------------------------------------------
# TRAIN / VALIDATION SPLIT
# ------------------------------------------------

train = model_df[
    model_df["date_"] < "2022-07-01"
]

validation = model_df[
    model_df["date_"] >= "2022-07-01"
]

print("\n========== TIME SPLIT ==========")

print(
    "Training rows:",
    len(train)
)

print(
    "Validation rows:",
    len(validation)
)

print(
    "Training period:",
    train["date_"].min(),
    "to",
    train["date_"].max()
)

print(
    "Validation period:",
    validation["date_"].min(),
    "to",
    validation["date_"].max()
)

# ------------------------------------------------
# SAMPLE
# ------------------------------------------------

print("\n========== SAMPLE ==========")

print(
    model_df[feature_columns]
    .head(10)
    .to_string(index=False)
)

# ------------------------------------------------
# DONE
# ------------------------------------------------

print("\n========== DONE ==========")
print("No output CSV was created.")