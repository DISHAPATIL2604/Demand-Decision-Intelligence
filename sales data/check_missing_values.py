import pandas as pd
from pathlib import Path

# ============================================================
# STEP 9: MISSING VALUES ANALYSIS
# ============================================================

project_root = Path(__file__).parent.parent

input_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_product_master.csv"
)

print("=" * 60)
print("MISSING VALUES ANALYSIS")
print("=" * 60)

print(f"\nFile:")
print(input_file)

print("\nReading data in chunks...")

chunk_size = 500_000

missing_counts = {}
total_rows = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(input_file, chunksize=chunk_size),
    start=1
):

    total_rows += len(chunk)

    # Count missing values
    for column in chunk.columns:
        missing = chunk[column].isna().sum()

        if column not in missing_counts:
            missing_counts[column] = 0

        missing_counts[column] += missing

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 60)
print("MISSING VALUES REPORT")
print("=" * 60)

print(f"\nTotal rows checked: {total_rows:,}")

print("\n" + "-" * 60)
print("COLUMN-WISE MISSING VALUES")
print("-" * 60)

for column, count in missing_counts.items():

    percentage = (count / total_rows) * 100

    print(
        f"{column}: "
        f"{count:,} missing "
        f"({percentage:.2f}%)"
    )


# ============================================================
# SUMMARY
# ============================================================

total_missing = sum(missing_counts.values())

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print(f"Total missing cells: {total_missing:,}")

columns_with_missing = sum(
    1 for count in missing_counts.values()
    if count > 0
)

print(
    f"Columns containing missing values: "
    f"{columns_with_missing}"
)

print("\nMissing value analysis completed!")