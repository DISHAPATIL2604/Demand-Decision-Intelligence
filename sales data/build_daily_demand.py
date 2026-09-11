import pandas as pd
import os

INPUT = "dataset/processed/sales_product_master_imputed.csv"
OUTPUT = "dataset/processed/daily_product_demand.csv"

USECOLS = [
    "date_",
    "product_id",
    "product_name",
    "city_name",
    "l0_category",
    "l1_category",
    "l2_category",
    "procured_quantity",
    "unit_selling_price",
    "order_id",
]

GROUP_COLS = [
    "date_",
    "product_id",
    "product_name",
    "city_name",
    "l0_category",
    "l1_category",
    "l2_category",
]

CHUNK_SIZE = 100_000

if os.path.exists(OUTPUT):
    os.remove(OUTPUT)

parts = []
total_rows = 0

for chunk_no, df in enumerate(
    pd.read_csv(
        INPUT,
        usecols=USECOLS,
        chunksize=CHUNK_SIZE
    ),
    start=1
):
    total_rows += len(df)

    df["revenue"] = (
        df["procured_quantity"] *
        df["unit_selling_price"]
    )

    grouped = (
        df.groupby(
            GROUP_COLS,
            dropna=False
        )
        .agg(
            daily_quantity=("procured_quantity", "sum"),
            daily_revenue=("revenue", "sum"),
            order_count=("order_id", "nunique")
        )
        .reset_index()
    )

    parts.append(grouped)

    if chunk_no % 20 == 0:
        print(
            f"Processed {total_rows:,} rows "
            f"({chunk_no} chunks)"
        )

print("\nCombining aggregated chunks...")

result = pd.concat(parts, ignore_index=True)

result = (
    result.groupby(
        GROUP_COLS,
        dropna=False
    )
    .agg(
        daily_quantity=("daily_quantity", "sum"),
        daily_revenue=("daily_revenue", "sum"),
        order_count=("order_count", "sum")
    )
    .reset_index()
)

result.to_csv(
    OUTPUT,
    index=False
)

print("\nDONE")
print(f"Input rows : {total_rows:,}")
print(f"Output rows: {len(result):,}")
print(f"Output     : {OUTPUT}")