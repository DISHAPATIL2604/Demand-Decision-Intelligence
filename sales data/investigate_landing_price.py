import pandas as pd
from pathlib import Path

# ============================================================
# STEP 10: LANDING PRICE INVESTIGATION
# ============================================================

project_root = Path(__file__).parent.parent

input_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_product_master.csv"
)

print("=" * 60)
print("LANDING PRICE MISSING VALUE INVESTIGATION")
print("=" * 60)

print(f"\nFile:")
print(input_file)

chunk_size = 500_000

total_rows = 0
missing_rows = 0
valid_rows = 0

missing_quantity = 0
missing_selling_price = 0
missing_both = 0

missing_by_month = {}
missing_by_city = {}

print("\nScanning data in chunks...")

for chunk_number, chunk in enumerate(
    pd.read_csv(input_file, chunksize=chunk_size),
    start=1
):

    total_rows += len(chunk)

    missing = chunk["total_weighted_landing_price"].isna()

    missing_count = missing.sum()

    missing_rows += missing_count
    valid_rows += len(chunk) - missing_count

    # Check other important fields
    missing_quantity += (
        missing & chunk["procured_quantity"].isna()
    ).sum()

    missing_selling_price += (
        missing & chunk["unit_selling_price"].isna()
    ).sum()

    missing_both += (
        missing
        & chunk["procured_quantity"].isna()
        & chunk["unit_selling_price"].isna()
    ).sum()

    # Month-wise missing values
    missing_data = chunk.loc[missing, ["date_"]].copy()

    if not missing_data.empty:

        missing_data["month"] = pd.to_datetime(
            missing_data["date_"],
            errors="coerce"
        ).dt.to_period("M").astype(str)

        month_counts = missing_data["month"].value_counts()

        for month, count in month_counts.items():
            missing_by_month[month] = (
                missing_by_month.get(month, 0) + count
            )

    # City-wise missing values
    city_counts = chunk.loc[
        missing, "city_name"
    ].value_counts()

    for city, count in city_counts.items():
        missing_by_city[city] = (
            missing_by_city.get(city, 0) + count
        )

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed | "
        f"Missing landing price={missing_rows:,}"
    )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 60)
print("LANDING PRICE REPORT")
print("=" * 60)

print(f"\nTotal rows: {total_rows:,}")
print(f"Valid landing price: {valid_rows:,}")
print(f"Missing landing price: {missing_rows:,}")

percentage = (missing_rows / total_rows) * 100

print(f"Missing percentage: {percentage:.2f}%")


print("\n" + "-" * 60)
print("RELATION WITH OTHER SALES FIELDS")
print("-" * 60)

print(
    f"Missing landing price + missing quantity: "
    f"{missing_quantity:,}"
)

print(
    f"Missing landing price + missing selling price: "
    f"{missing_selling_price:,}"
)

print(
    f"Missing landing price + both missing: "
    f"{missing_both:,}"
)


# ============================================================
# MONTH-WISE
# ============================================================

print("\n" + "-" * 60)
print("MONTH-WISE MISSING LANDING PRICE")
print("-" * 60)

for month in sorted(missing_by_month):
    print(
        f"{month}: "
        f"{missing_by_month[month]:,}"
    )


# ============================================================
# CITY-WISE TOP 20
# ============================================================

print("\n" + "-" * 60)
print("TOP 20 CITIES WITH MISSING LANDING PRICE")
print("-" * 60)

top_cities = sorted(
    missing_by_city.items(),
    key=lambda x: x[1],
    reverse=True
)[:20]

for city, count in top_cities:
    print(
        f"{city}: "
        f"{count:,}"
    )


print("\n" + "=" * 60)
print("INVESTIGATION COMPLETED")
print("=" * 60)