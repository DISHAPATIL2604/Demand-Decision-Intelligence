import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = BASE_DIR / "dataset" / "processed" / "sales_product_master_imputed.csv"

print("Reading dataset...")
df = pd.read_csv(FILE)

df["revenue"] = df["procured_quantity"] * df["unit_selling_price"]

print("\n========== L0 CATEGORY ANALYSIS ==========")

l0 = (
    df.groupby("l0_category", dropna=False)
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum"),
          products=("product_id", "nunique")
      )
      .sort_values("revenue", ascending=False)
)

l0["revenue_share_%"] = (
    l0["revenue"] / l0["revenue"].sum() * 100
)

print(l0)

print("\n========== TOP 15 L1 CATEGORIES ==========")

l1 = (
    df.groupby("l1_category", dropna=False)
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum"),
          products=("product_id", "nunique")
      )
      .sort_values("revenue", ascending=False)
      .head(15)
)

print(l1)

print("\n========== TOP 15 L2 CATEGORIES ==========")

l2 = (
    df.groupby("l2_category", dropna=False)
      .agg(
          quantity=("procured_quantity", "sum"),
          revenue=("revenue", "sum"),
          products=("product_id", "nunique")
      )
      .sort_values("revenue", ascending=False)
      .head(15)
)

print(l2)

print("\n========== L0 CATEGORY SHARE ==========")

print(
    l0[["revenue", "revenue_share_%"]]
)

print("\n========== DONE ==========")