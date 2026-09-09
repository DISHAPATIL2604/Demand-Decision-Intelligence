import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# 2. PRODUCT MASTER FILE
# ==========================================

product_file = (
    project_root
    / "dataset"
    / "raw"
    / "products"
    / "dim_product.csv"
)


print("=" * 60)
print("PRODUCT MASTER VALIDATION")
print("=" * 60)

print("\nFile:")
print(product_file)


# ==========================================
# 3. CHECK FILE
# ==========================================

if not product_file.exists():
    print("\nERROR: dim_product.csv not found!")
    exit()


# ==========================================
# 4. READ DATA
# ==========================================

df = pd.read_csv(
    product_file,
    low_memory=False
)


# ==========================================
# 5. BASIC INFORMATION
# ==========================================

print("\n" + "=" * 60)
print("BASIC INFORMATION")
print("=" * 60)

print(f"\nTotal rows: {len(df):,}")
print(f"Total columns: {len(df.columns)}")


print("\nColumns:")
for i, column in enumerate(df.columns, start=1):
    print(f"{i}. {column}")


# ==========================================
# 6. DATA TYPES
# ==========================================

print("\n" + "=" * 60)
print("DATA TYPES")
print("=" * 60)

print(df.dtypes)


# ==========================================
# 7. MISSING VALUES
# ==========================================

print("\n" + "=" * 60)
print("MISSING VALUES")
print("=" * 60)

missing = df.isnull().sum()

for column, count in missing.items():

    percentage = (
        count / len(df) * 100
        if len(df) > 0
        else 0
    )

    print(
        f"{column}: "
        f"{count:,} missing "
        f"({percentage:.2f}%)"
    )


# ==========================================
# 8. DUPLICATE PRODUCT IDs
# ==========================================

print("\n" + "=" * 60)
print("PRODUCT ID VALIDATION")
print("=" * 60)

if "product_id" in df.columns:

    total_product_ids = df["product_id"].notna().sum()

    unique_product_ids = df["product_id"].nunique()

    duplicate_product_rows = (
        df["product_id"].duplicated(keep=False).sum()
    )

    missing_product_ids = (
        df["product_id"].isna().sum()
    )

    print(
        f"\nNon-null product IDs: "
        f"{total_product_ids:,}"
    )

    print(
        f"Unique product IDs: "
        f"{unique_product_ids:,}"
    )

    print(
        f"Rows with duplicate product IDs: "
        f"{duplicate_product_rows:,}"
    )

    print(
        f"Missing product IDs: "
        f"{missing_product_ids:,}"
    )


# ==========================================
# 9. DUPLICATE ROWS
# ==========================================

print("\n" + "=" * 60)
print("DUPLICATE ROW VALIDATION")
print("=" * 60)

duplicate_rows = df.duplicated().sum()

print(
    f"\nExact duplicate rows: "
    f"{duplicate_rows:,}"
)


# ==========================================
# 10. UNIQUE VALUES
# ==========================================

print("\n" + "=" * 60)
print("UNIQUE VALUE COUNTS")
print("=" * 60)

columns_to_check = [
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

for column in columns_to_check:

    if column in df.columns:

        print(
            f"{column}: "
            f"{df[column].nunique(dropna=True):,} unique"
        )


# ==========================================
# 11. SAMPLE DATA
# ==========================================

print("\n" + "=" * 60)
print("FIRST 5 RECORDS")
print("=" * 60)

print(
    df.head(5).to_string(index=False)
)


# ==========================================
# 12. FINAL STATUS
# ==========================================

print("\n" + "=" * 60)
print("PRODUCT MASTER VALIDATION COMPLETED")
print("=" * 60)