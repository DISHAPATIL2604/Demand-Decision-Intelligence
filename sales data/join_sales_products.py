import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

project_root = Path(__file__).parent.parent


# ============================================================
# FILE PATHS
# ============================================================

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

output_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_product_master.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 60)
print("SALES + PRODUCT MASTER JOIN")
print("=" * 60)

print(f"\nSales file:")
print(sales_file)

print(f"\nProduct master:")
print(product_file)

print(f"\nOutput:")
print(output_file)


# ============================================================
# READ PRODUCT MASTER
# ============================================================

print("\n" + "=" * 60)
print("READING PRODUCT MASTER")
print("=" * 60)

product_columns = [
    "product_id",
    "product_name",
    "unit",
    "product_type",
    "brand_name",
    "manufacturer_name",
    "l0_category",
    "l1_category",
    "l2_category",
    "l0_category_id",
    "l1_category_id",
    "l2_category_id"
]

products = pd.read_csv(
    product_file,
    usecols=product_columns,
    low_memory=False
)


# Make product_id numeric
products["product_id"] = pd.to_numeric(
    products["product_id"],
    errors="coerce"
)


# Remove impossible product master rows
products = products.dropna(
    subset=["product_id"]
)


products["product_id"] = products[
    "product_id"
].astype("int64")


print(
    f"Product master rows: "
    f"{len(products):,}"
)


print(
    f"Unique product IDs: "
    f"{products['product_id'].nunique():,}"
)


# ============================================================
# CHECK DUPLICATES
# ============================================================

duplicate_products = products[
    products["product_id"].duplicated(keep=False)
]

if len(duplicate_products) > 0:

    print(
        f"\nWARNING: "
        f"{len(duplicate_products):,} duplicate product rows found."
    )

    print("Keeping first occurrence of each product_id.")

    products = products.drop_duplicates(
        subset=["product_id"],
        keep="first"
    )

else:

    print("\nNo duplicate product IDs found. ✓")


# ============================================================
# DELETE OLD OUTPUT IF EXISTS
# ============================================================

if output_file.exists():

    output_file.unlink()

    print("\nOld sales_product_master.csv removed.")


# ============================================================
# PROCESS SALES IN CHUNKS
# ============================================================

print("\n" + "=" * 60)
print("JOINING SALES WITH PRODUCT MASTER")
print("=" * 60)

chunk_size = 500_000

total_input = 0
total_output = 0
matched_rows = 0
unmatched_rows = 0

first_chunk = True


for chunk_number, sales in enumerate(
    pd.read_csv(
        sales_file,
        chunksize=chunk_size,
        low_memory=False
    ),
    start=1
):

    # --------------------------------------------------------
    # Convert product_id
    # --------------------------------------------------------

    sales["product_id"] = pd.to_numeric(
        sales["product_id"],
        errors="coerce"
    )


    # --------------------------------------------------------
    # LEFT JOIN
    # --------------------------------------------------------

    merged = sales.merge(
        products,
        on="product_id",
        how="left",
        indicator=True
    )


    # --------------------------------------------------------
    # MATCH COUNTS
    # --------------------------------------------------------

    matched = (
        merged["_merge"] == "both"
    ).sum()

    unmatched = (
        merged["_merge"] == "left_only"
    ).sum()


    # Remove merge indicator
    merged.drop(
        columns=["_merge"],
        inplace=True
    )


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    total_input += len(sales)
    total_output += len(merged)

    matched_rows += matched
    unmatched_rows += unmatched


    # --------------------------------------------------------
    # WRITE OUTPUT
    # --------------------------------------------------------

    merged.to_csv(
        output_file,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False


    print(
        f"Chunk {chunk_number}: "
        f"Input={len(sales):,} | "
        f"Output={len(merged):,} | "
        f"Matched={matched:,} | "
        f"Unmatched={unmatched:,}"
    )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 60)
print("JOIN COMPLETED")
print("=" * 60)

print(
    f"\nTotal input sales rows: "
    f"{total_input:,}"
)

print(
    f"Total output rows: "
    f"{total_output:,}"
)

print(
    f"Matched rows: "
    f"{matched_rows:,}"
)

print(
    f"Unmatched rows: "
    f"{unmatched_rows:,}"
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("ROW COUNT VALIDATION")
print("=" * 60)

if total_input == total_output:

    print(
        "\n✓ Row count preserved."
    )

else:

    print(
        "\n⚠ WARNING: Row count changed!"
    )


# ============================================================
# MATCH RATE
# ============================================================

if total_input > 0:

    match_rate = (
        matched_rows / total_input
    ) * 100

    unmatched_rate = (
        unmatched_rows / total_input
    ) * 100

    print(
        f"\nMatch rate: "
        f"{match_rate:.2f}%"
    )

    print(
        f"Unmatched rate: "
        f"{unmatched_rate:.2f}%"
    )


# ============================================================
# OUTPUT
# ============================================================

print("\nOutput file created at:")

print(output_file)

print("\n" + "=" * 60)
print("STEP 8 COMPLETED")
print("=" * 60)