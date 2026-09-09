import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

# combine_sales.py is inside "sales data"
# So we go two levels up to reach project root

project_root = Path(__file__).parent.parent


# ==========================================
# 2. INPUT & OUTPUT FOLDERS
# ==========================================

# Raw sales files
sales_folder = project_root / "dataset" / "raw" / "sales"

# Combined output folder
output_folder = project_root / "dataset" / "combined"

# Create output folder if it doesn't exist
output_folder.mkdir(parents=True, exist_ok=True)


# ==========================================
# 3. SALES FILES
# ==========================================

files = [
    "fact_sales_apr1.csv",
    "fact_sales_apr2.csv",
    "fact_sales_may1.csv",
    "fact_sales_may2.csv",
    "fact_sales_jun1.csv",
    "fact_sales_jun2.csv",
    "fact_sales_jul1.csv"
]


# ==========================================
# 4. OUTPUT FILE
# ==========================================

output = output_folder / "fact_sales_combined.csv"


# ==========================================
# 5. COMBINE ALL FILES
# ==========================================

first_file = True
total_rows = 0

for file in files:

    path = sales_folder / file

    print(f"\nReading: {file}")

    # Check if file exists
    if not path.exists():
        print(f"ERROR: File not found -> {path}")
        continue

    # Read CSV
    df = pd.read_csv(path)

    rows = len(df)
    total_rows += rows

    # Add data to combined CSV
    df.to_csv(
        output,
        mode="w" if first_file else "a",
        header=first_file,
        index=False
    )

    first_file = False

    print(f"Added {rows:,} rows")


# ==========================================
# 6. FINAL MESSAGE
# ==========================================

print("\n" + "=" * 50)
print("DONE!")
print("=" * 50)

print(f"Total rows combined: {total_rows:,}")
print(f"Output file: {output}")