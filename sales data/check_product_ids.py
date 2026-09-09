import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# 2. FILE PATHS
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
# 3. HEADER
# ==========================================

print("=" * 60)
print("PRODUCT ID RELATIONSHIP CHECK")
print("=" * 60)


# ==========================================
# 4. CHECK FILES
# ==========================================

if not sales_file.exists():
    print("\nERROR: sales_cleaned.csv not found!")
    print(sales_file)
    exit()

if not product_file.exists():
    print("\nERROR: dim_product.csv not found!")
    print(product_file)
    exit()


# ==========================================
# 5. READ PRODUCT MASTER
# ==========================================

print("\nReading product master...")

products = pd.read_csv(
    product_file,
    usecols=["product_id"]
)

# Remove missing IDs just in case
products = products.dropna(subset=["product_id"])

# Make sure both datasets use the same type
products["product_id"] = pd.to_numeric(
    products["product_id"],
    errors="coerce"
)

product_ids = set(
    products["product_id"].dropna().astype("int64")
)


print(
    f"Unique product IDs in master: "
    f"{len(product_ids):,}"
)


# ==========================================
# 6. PROCESS SALES IN CHUNKS
# ==========================================

chunk_size = 500_000

total_sales_rows = 0
matched_rows = 0
unmatched_rows = 0

all_sales_product_ids = set()

chunk_number = 0


print("\nReading sales data in chunks...\n")


for df in pd.read_csv(
    sales_file,
    usecols=["product_id"],
    chunksize=chunk_size,
    low_memory=False
):

    chunk_number += 1

    total_sales_rows += len(df)


    # Convert product_id to numeric
    df["product_id"] = pd.to_numeric(
        df["product_id"],
        errors="coerce"
    )


    # Remove missing product IDs for relationship check
    valid_ids = df["product_id"].dropna().astype("int64")


    # Store unique sales product IDs
    all_sales_product_ids.update(
        valid_ids.unique()
    )


    # Check whether product exists in master
    matched = valid_ids.isin(product_ids)

    matched_count = matched.sum()
    unmatched_count = len(valid_ids) - matched_count


    matched_rows += matched_count
    unmatched_rows += unmatched_count


    print(
        f"Chunk {chunk_number}: "
        f"{total_sales_rows:,} rows processed | "
        f"Matched={matched_count:,} | "
        f"Unmatched={unmatched_count:,}"
    )


# ==========================================
# 7. UNIQUE PRODUCT ID MATCH
# ==========================================

matched_unique_ids = (
    all_sales_product_ids.intersection(product_ids)
)

unmatched_unique_ids = (
    all_sales_product_ids - product_ids
)


# ==========================================
# 8. FINAL REPORT
# ==========================================

print("\n" + "=" * 60)
print("FINAL RELATIONSHIP REPORT")
print("=" * 60)

print(
    f"\nTotal sales rows checked: "
    f"{total_sales_rows:,}"
)

print(
    f"Unique product IDs in sales: "
    f"{len(all_sales_product_ids):,}"
)

print(
    f"Unique product IDs in product master: "
    f"{len(product_ids):,}"
)

print(
    f"\nMatched unique product IDs: "
    f"{len(matched_unique_ids):,}"
)

print(
    f"Unmatched unique product IDs: "
    f"{len(unmatched_unique_ids):,}"
)

print(
    f"\nMatched sales rows: "
    f"{matched_rows:,}"
)

print(
    f"Unmatched sales rows: "
    f"{unmatched_rows:,}"
)


# ==========================================
# 9. MATCH PERCENTAGE
# ==========================================

if total_sales_rows > 0:

    match_percentage = (
        matched_rows / total_sales_rows
    ) * 100

    unmatched_percentage = (
        unmatched_rows / total_sales_rows
    ) * 100

    print(
        f"\nSales row match rate: "
        f"{match_percentage:.2f}%"
    )

    print(
        f"Sales row unmatched rate: "
        f"{unmatched_percentage:.2f}%"
    )


# ==========================================
# 10. SHOW UNMATCHED IDs
# ==========================================

print("\n" + "=" * 60)
print("UNMATCHED PRODUCT IDs")
print("=" * 60)

if len(unmatched_unique_ids) == 0:

    print("\nAll sales product IDs exist in product master. ✅")

else:

    print(
        f"\nFound {len(unmatched_unique_ids):,} "
        f"unmatched product IDs."
    )

    print("\nFirst 20 unmatched IDs:")

    for product_id in sorted(unmatched_unique_ids)[:20]:
        print(product_id)


# ==========================================
# 11. COMPLETED
# ==========================================

print("\n" + "=" * 60)
print("PRODUCT ID RELATIONSHIP CHECK COMPLETED")
print("=" * 60)