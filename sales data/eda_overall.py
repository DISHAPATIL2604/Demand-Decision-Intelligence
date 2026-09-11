import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = BASE_DIR / "dataset" / "processed" / "sales_product_master_imputed.csv"

print("Reading dataset...")
df = pd.read_csv(FILE)

print("\n========== BASIC INFORMATION ==========")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())

print("\n========== DATE ==========")

df["date_"] = pd.to_datetime(df["date_"], errors="coerce")

print("Start date:", df["date_"].min())
print("End date:", df["date_"].max())
print("Missing dates:", df["date_"].isna().sum())

print("\n========== SALES METRICS ==========")

print("Total quantity:", df["procured_quantity"].sum())

print(
    "Total revenue:",
    (df["procured_quantity"] * df["unit_selling_price"]).sum()
)

print(
    "Total discount:",
    df["total_discount_amount"].sum()
)

print("\n========== MISSING VALUES ==========")

missing = df.isna().sum()
missing = missing[missing > 0].sort_values(ascending=False)

print(missing)

print("\n========== UNIQUE VALUES ==========")

for col in ["product_id", "city_name", "l0_category", "l1_category", "l2_category"]:
    if col in df.columns:
        print(f"{col}: {df[col].nunique()}")

print("\n========== CITY SALES ==========")

city_sales = (
    df.groupby("city_name")
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("unit_selling_price", 
                   lambda x: 0)
      )
)

# Calculate revenue separately
df["revenue"] = df["procured_quantity"] * df["unit_selling_price"]

city_sales = (
    df.groupby("city_name")
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum")
      )
      .sort_values("revenue", ascending=False)
)

print(city_sales)

print("\n========== DAILY REVENUE ==========")

daily = (
    df.groupby("date_")
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum")
      )
      .sort_index()
)

print(daily.head())
print("\nHighest revenue day:")
print(daily["revenue"].idxmax(), daily["revenue"].max())

print("\nLowest revenue day:")
print(daily["revenue"].idxmin(), daily["revenue"].min())

print("\n========== TOP 10 PRODUCTS BY REVENUE ==========")

top_products = (
    df.groupby(["product_id", "product_name"], dropna=False)
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum")
      )
      .sort_values("revenue", ascending=False)
      .head(10)
)

print(top_products)

print("\n========== DONE ==========")