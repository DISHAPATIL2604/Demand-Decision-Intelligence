import pandas as pd
from pathlib import Path

# 1. PROJECT ROOT
# validate_combined.py is inside "sales data"
project_root = Path(__file__).parent.parent
# 2. COMBINED SALES FILE

file_path = (
    project_root
    / "dataset"
    / "combined"
    / "fact_sales_combined.csv"
)

# 3. EXPECTED COLUMNS

expected_columns = [
    "Unnamed: 0",
    "date_",
    "city_name",
    "order_id",
    "cart_id",
    "dim_customer_key",
    "procured_quantity",
    "unit_selling_price",
    "total_discount_amount",
    "product_id",
    "total_weighted_landing_price"
]



# 4. CHECK FILE

if not file_path.exists():
    print("ERROR: Combined file not found!")
    print(file_path)
    exit()


print("=" * 60)
print("COMBINED SALES DATA VALIDATION")
print("=" * 60)

print(f"\nFile:")
print(file_path)

# 5. READ HEADER

header = pd.read_csv(file_path, nrows=0)

actual_columns = list(header.columns)

print("\nColumns found:")
for column in actual_columns:
    print(f" - {column}")

# 6. COLUMN CHECK

print("\n" + "=" * 60)
print("COLUMN CHECK")
print("=" * 60)

missing_columns = [
    column
    for column in expected_columns
    if column not in actual_columns
]

extra_columns = [
    column
    for column in actual_columns
    if column not in expected_columns
]

if not missing_columns and not extra_columns:
    print("✓ All expected columns are present.")
else:

    if missing_columns:
        print("\nMissing columns:")
        for column in missing_columns:
            print(f" - {column}")

    if extra_columns:
        print("\nExtra columns:")
        for column in extra_columns:
            print(f" - {column}")

# 7. CHUNK-WISE VALIDATION

chunk_size = 500_000

total_rows = 0

missing_values = {
    column: 0
    for column in actual_columns
}

duplicate_rows = 0

min_date = None
max_date = None

negative_quantity = 0
negative_price = 0
negative_discount = 0

unique_products = set()
unique_cities = set()


print("\n" + "=" * 60)
print("READING DATA IN CHUNKS")
print("=" * 60)


for chunk_number, df in enumerate(
    pd.read_csv(
        file_path,
        chunksize=chunk_size,
        low_memory=False
    ),
    start=1
):

    rows = len(df)

    total_rows += rows

    print(
        f"Chunk {chunk_number}: "
        f"{rows:,} rows | "
        f"Total processed: {total_rows:,}"
    )


    # Missing values

    for column in actual_columns:

        missing_values[column] += (
            df[column].isna().sum()
        )

    # Duplicate rows

    duplicate_rows += df.duplicated().sum()

    # Date validation

    dates = pd.to_datetime(
        df["date_"],
        errors="coerce",
        dayfirst=True
    )

    valid_dates = dates.dropna()

    if not valid_dates.empty:

        chunk_min_date = valid_dates.min()
        chunk_max_date = valid_dates.max()

        if min_date is None or chunk_min_date < min_date:
            min_date = chunk_min_date

        if max_date is None or chunk_max_date > max_date:
            max_date = chunk_max_date

    # Negative quantity

    negative_quantity += (
        (df["procured_quantity"] < 0).sum()
    )


    # Negative price

    negative_price += (
        (df["unit_selling_price"] < 0).sum()
    )


    # Negative discount

    negative_discount += (
        (df["total_discount_amount"] < 0).sum()
    )

    # Unique products

    unique_products.update(
        df["product_id"].dropna().unique()
    )

    # Unique cities

    unique_cities.update(
        df["city_name"].dropna().unique()
    )

# 8. FINAL REPORT

print("\n" + "=" * 60)
print("FINAL VALIDATION REPORT")
print("=" * 60)


print(f"\nTotal rows:")
print(f"{total_rows:,}")


print(f"\nExpected rows from combining:")
print(f"{46_706_387:,}")


if total_rows == 46_706_387:
    print("✓ Row count matches.")
else:
    print("⚠ Row count does NOT match.")

# 9. MISSING VALUES


print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

total_missing = 0

for column, count in missing_values.items():

    total_missing += count

    print(
        f"{column}: {count:,}"
    )

print(f"\nTotal missing values: {total_missing:,}")



# 10. DUPLICATES

print("\n" + "=" * 60)
print("DUPLICATES")
print("=" * 60)

print(
    f"Duplicate rows found: {duplicate_rows:,}"
)


# ==========================================
# 11. DATE RANGE
# ==========================================

print("\n" + "=" * 60)
print("DATE RANGE")
print("=" * 60)

print(f"Minimum date: {min_date}")
print(f"Maximum date: {max_date}")


# ==========================================
# 12. NEGATIVE VALUES
# ==========================================

print("\n" + "=" * 60)
print("NEGATIVE VALUES")
print("=" * 60)

print(
    f"Negative quantity: {negative_quantity:,}"
)

print(
    f"Negative selling price: {negative_price:,}"
)

print(
    f"Negative discount: {negative_discount:,}"
)


# ==========================================
# 13. UNIQUE VALUES
# ==========================================

print("\n" + "=" * 60)
print("UNIQUE VALUES")
print("=" * 60)

print(
    f"Unique products: {len(unique_products):,}"
)

print(
    f"Unique cities: {len(unique_cities):,}"
)
# 14. DONE


print("\n" + "=" * 60)
print("VALIDATION COMPLETED!")
print("=" * 60)