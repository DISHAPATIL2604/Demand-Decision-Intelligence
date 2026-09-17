import pandas as pd
import os

SALES_FILE = "dataset/cleaned/sales_product_master.csv"
PRODUCT_FILE = "dataset/cleaned/dim_product_cleaned_with_audit.csv"
OUTPUT_FILE = "dataset/cleaned/sales_product_master_recovered.csv"

CHUNK_SIZE = 500_000

print("=" * 60)
print("RECOVERING PRODUCT ATTRIBUTES")
print("=" * 60)

# ---------------------------------------------------------
# Load cleaned product master
# ---------------------------------------------------------
print("\nLoading cleaned product master...")

products = pd.read_csv(
    PRODUCT_FILE,
    usecols=["product_id", "brand_name", "manufacturer_name"]
)

products = products.drop_duplicates("product_id")

brand_map = products.set_index("product_id")["brand_name"]
manufacturer_map = products.set_index("product_id")["manufacturer_name"]

print(f"Products loaded: {len(products):,}")

# ---------------------------------------------------------
# Process sales in chunks
# ---------------------------------------------------------
total_rows = 0
brand_filled = 0
manufacturer_filled = 0

first_chunk = True

print("\nProcessing sales file...")

for chunk_no, chunk in enumerate(
    pd.read_csv(SALES_FILE, chunksize=CHUNK_SIZE),
    start=1
):

    total_rows += len(chunk)

    # Missing detection
    brand_missing = (
        chunk["brand_name"].isna()
        | (chunk["brand_name"].astype("string").str.strip() == "")
    )

    manufacturer_missing = (
        chunk["manufacturer_name"].isna()
        | (chunk["manufacturer_name"].astype("string").str.strip() == "")
    )

    # Lookup from cleaned product master
    mapped_brand = chunk["product_id"].map(brand_map)
    mapped_manufacturer = chunk["product_id"].map(manufacturer_map)

    # Only fill missing values
    brand_fill = brand_missing & mapped_brand.notna()
    manufacturer_fill = manufacturer_missing & mapped_manufacturer.notna()

    brand_filled += brand_fill.sum()
    manufacturer_filled += manufacturer_fill.sum()

    chunk.loc[brand_fill, "brand_name"] = mapped_brand[brand_fill]
    chunk.loc[manufacturer_fill, "manufacturer_name"] = (
        mapped_manufacturer[manufacturer_fill]
    )

    # Write chunk
    chunk.to_csv(
        OUTPUT_FILE,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False

    print(
        f"Chunk {chunk_no}: "
        f"{total_rows:,} rows processed | "
        f"Brand filled: {brand_filled:,} | "
        f"Manufacturer filled: {manufacturer_filled:,}"
    )

# ---------------------------------------------------------
# Final report
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("RECOVERY COMPLETED")
print("=" * 60)

print(f"Total rows:          {total_rows:,}")
print(f"Brand filled:        {brand_filled:,}")
print(f"Manufacturer filled: {manufacturer_filled:,}")
print(f"Output:              {OUTPUT_FILE}")

print("\nOriginal sales file has NOT been modified.")