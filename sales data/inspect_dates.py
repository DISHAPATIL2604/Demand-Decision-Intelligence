import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# 2. COMBINED FILE
# ==========================================

file_path = (
    project_root
    / "dataset"
    / "combined"
    / "fact_sales_combined.csv"
)


# ==========================================
# 3. READ ONLY DATE COLUMN
# ==========================================

print("=" * 60)
print("DATE FORMAT INSPECTION")
print("=" * 60)

df = pd.read_csv(
    file_path,
    usecols=["date_"],
    nrows=100
)


# ==========================================
# 4. SHOW RAW DATE VALUES
# ==========================================

print("\nFirst 30 raw date values:\n")

for i, value in enumerate(df["date_"].head(30), start=1):
    print(f"{i}. {repr(value)}")


# ==========================================
# 5. SHOW DATA TYPE
# ==========================================

print("\n" + "=" * 60)
print("DATA TYPE")
print("=" * 60)

print(df["date_"].dtype)


# ==========================================
# 6. TRY DIFFERENT DATE PARSING METHODS
# ==========================================

print("\n" + "=" * 60)
print("DATE PARSING TEST")
print("=" * 60)


# Method 1: dayfirst=True
dates_dayfirst = pd.to_datetime(
    df["date_"],
    errors="coerce",
    dayfirst=True
)

print(
    "\nUsing dayfirst=True:"
)
print(
    f"Invalid dates: {dates_dayfirst.isna().sum()}"
)


# Method 2: dayfirst=False
dates_normal = pd.to_datetime(
    df["date_"],
    errors="coerce",
    dayfirst=False
)

print(
    "\nUsing dayfirst=False:"
)
print(
    f"Invalid dates: {dates_normal.isna().sum()}"
)


# ==========================================
# 7. SHOW PARSED RESULTS
# ==========================================

print("\n" + "=" * 60)
print("PARSED DATE COMPARISON")
print("=" * 60)

comparison = pd.DataFrame({
    "raw_date": df["date_"].head(20),
    "dayfirst_true": dates_dayfirst.head(20),
    "dayfirst_false": dates_normal.head(20)
})

print(comparison.to_string(index=False))


# ==========================================
# 8. DONE
# ==========================================

print("\n" + "=" * 60)
print("INSPECTION COMPLETED")
print("=" * 60)