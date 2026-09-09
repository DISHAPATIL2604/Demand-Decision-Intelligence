import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# 2. COMBINED SALES FILE
# ==========================================

file_path = (
    project_root
    / "dataset"
    / "combined"
    / "fact_sales_combined.csv"
)


# ==========================================
# 3. CHECK FILE
# ==========================================

if not file_path.exists():
    print("ERROR: Combined sales file not found!")
    print(file_path)
    exit()


print("=" * 60)
print("DATE DISTRIBUTION CHECK")
print("=" * 60)

print(f"\nFile:")
print(file_path)


# ==========================================
# 4. READ ONLY DATE COLUMN
# ==========================================

monthly_counts = {}

total_rows = 0
invalid_dates = 0


print("\nReading data in chunks...\n")


for chunk_number, df in enumerate(
    pd.read_csv(
        file_path,
        usecols=["date_"],
        chunksize=500_000
    ),
    start=1
):

    total_rows += len(df)

    # Convert date
    dates = pd.to_datetime(
    df["date_"],
    errors="coerce",
    format="%Y-%m-%d"
)

    # Count invalid dates
    invalid_dates += dates.isna().sum()

    # Get month
    months = dates.dropna().dt.to_period("M")

    # Count months in this chunk
    counts = months.value_counts()

    for month, count in counts.items():

        month = str(month)

        monthly_counts[month] = (
            monthly_counts.get(month, 0) + count
        )

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


# ==========================================
# 5. MONTHLY REPORT
# ==========================================

print("\n" + "=" * 60)
print("MONTH-WISE SALES RECORDS")
print("=" * 60)

for month in sorted(monthly_counts):

    print(
        f"{month}: "
        f"{monthly_counts[month]:,} rows"
    )


# ==========================================
# 6. FINAL SUMMARY
# ==========================================

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Total rows checked: {total_rows:,}")

print(
    f"Invalid/missing dates: "
    f"{invalid_dates:,}"
)

print(
    f"Number of months found: "
    f"{len(monthly_counts)}"
)

print("\nDate distribution check completed!")