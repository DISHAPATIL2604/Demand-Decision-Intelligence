import pandas as pd
from pathlib import Path


# ==========================================
# PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# FILES
# ==========================================

sales_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_cleaned.csv"
)

product_file = (
    project_root
    / "dataset"
    / "raw"
    / "products"
    / "dim_product.csv"
)


# ==========================================
# HEADER
# ==========================================

print("=" * 60)
print("UNMATCHED PRODUCT INVESTIGATION")
print("=" * 60)


# ==========================================
# READ PRODUCT MASTER
# ==========================================

print("\nReading product master...")

products = pd.read_csv(
    product_file,
    usecols=["product_id"]
)

products["product_id"] = pd.to_numeric(
    products["product_id"],
    errors="coerce"
)

master_ids = set(
    products["product_id"]
    .dropna()
    .astype("int64")
)


# ==========================================
# FIND UNMATCHED IDs
# ==========================================

print("Finding unmatched product IDs...")


sales_ids = set()

for chunk in pd.read_csv(
    sales_file,
    usecols=["product_id"],
    chunksize=500_000,
    low_memory=False
):

    chunk["product_id"] = pd.to_numeric(
        chunk["product_id"],
        errors="coerce"
    )

    ids = chunk["product_id"].dropna().astype("int64")

    sales_ids.update(ids.unique())


unmatched_ids = sales_ids - master_ids


print(
    f"\nUnmatched unique product IDs: "
    f"{len(unmatched_ids):,}"
)


# ==========================================
# INVESTIGATE SALES IMPACT
# ==========================================

total_rows = 0
total_quantity = 0
total_revenue = 0
total_discount = 0


print("\nScanning sales data...\n")


for chunk in pd.read_csv(
    sales_file,
    usecols=[
        "product_id",
        "procured_quantity",
        "unit_selling_price",
        "total_discount_amount"
    ],
    chunksize=500_000,
    low_memory=False
):

    chunk["product_id"] = pd.to_numeric(
        chunk["product_id"],
        errors="coerce"
    )

    chunk["procured_quantity"] = pd.to_numeric(
        chunk["procured_quantity"],
        errors="coerce"
    ).fillna(0)

    chunk["unit_selling_price"] = pd.to_numeric(
        chunk["unit_selling_price"],
        errors="coerce"
    ).fillna(0)

    chunk["total_discount_amount"] = pd.to_numeric(
        chunk["total_discount_amount"],
        errors="coerce"
    ).fillna(0)


    unmatched = chunk[
        chunk["product_id"].isin(unmatched_ids)
    ]


    if len(unmatched) > 0:

        total_rows += len(unmatched)

        total_quantity += (
            unmatched["procured_quantity"].sum()
        )

        total_revenue += (
            unmatched["procured_quantity"]
            * unmatched["unit_selling_price"]
        ).sum()

        total_discount += (
            unmatched["total_discount_amount"].sum()
        )


# ==========================================
# FINAL REPORT
# ==========================================

print("\n" + "=" * 60)
print("UNMATCHED PRODUCT IMPACT")
print("=" * 60)

print(
    f"\nUnmatched sales records: "
    f"{total_rows:,}"
)

print(
    f"Unmatched sales quantity: "
    f"{total_quantity:,.2f}"
)

print(
    f"Estimated sales value: "
    f"{total_revenue:,.2f}"
)

print(
    f"Total discount amount: "
    f"{total_discount:,.2f}"
)


# ==========================================
# PERCENTAGE
# ==========================================

print("\n" + "=" * 60)
print("IMPACT PERCENTAGES")
print("=" * 60)


# Total sales rows
total_sales_rows = 46_706_387


if total_sales_rows > 0:

    row_percentage = (
        total_rows / total_sales_rows
    ) * 100

    print(
        f"\nUnmatched rows percentage: "
        f"{row_percentage:.2f}%"
    )


# ==========================================
# COMPLETED
# ==========================================

print("\n" + "=" * 60)
print("INVESTIGATION COMPLETED")
print("=" * 60)