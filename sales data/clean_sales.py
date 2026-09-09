import pandas as pd
from pathlib import Path


# ==========================================
# 1. PROJECT ROOT
# ==========================================

project_root = Path(__file__).parent.parent


# ==========================================
# 2. INPUT & OUTPUT
# ==========================================

input_file = (
    project_root
    / "dataset"
    / "combined"
    / "fact_sales_combined.csv"
)

output_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_cleaned.csv"
)


# ==========================================
# 3. FINAL COLUMNS
# ==========================================

final_columns = [
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


# ==========================================
# 4. CHECK INPUT
# ==========================================

if not input_file.exists():
    print("ERROR: Combined sales file not found!")
    print(input_file)
    exit()


# ==========================================
# 5. CREATE OUTPUT FOLDER
# ==========================================

output_file.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# 6. DELETE OLD CLEANED FILE
# ==========================================

if output_file.exists():
    output_file.unlink()
    print("Old sales_cleaned.csv removed.")


# ==========================================
# 7. PROCESS DATA
# ==========================================

chunk_size = 500_000

total_input_rows = 0
total_output_rows = 0
total_removed_rows = 0
total_missing_landing_price = 0

first_chunk = True


print("=" * 60)
print("SALES DATA CLEANING")
print("=" * 60)

print(f"\nInput:")
print(input_file)

print(f"\nOutput:")
print(output_file)

print("\nProcessing chunks...\n")


for chunk_number, df in enumerate(
    pd.read_csv(
        input_file,
        chunksize=chunk_size,
        low_memory=False
    ),
    start=1
):

    input_rows = len(df)
    total_input_rows += input_rows


    # ======================================
    # 8. KEEP ONLY REQUIRED COLUMNS
    # ======================================

    df = df[final_columns]


    # ======================================
    # 9. DATE CONVERSION
    # ======================================

    df["date_"] = pd.to_datetime(
        df["date_"],
        format="%Y-%m-%d",
        errors="coerce"
    )


    # ======================================
    # 10. NUMERIC COLUMNS
    # ======================================

    numeric_columns = [
        "procured_quantity",
        "unit_selling_price",
        "total_discount_amount",
        "total_weighted_landing_price"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    # ======================================
    # 11. COUNT MISSING LANDING PRICE
    # ======================================

    total_missing_landing_price += (
        df["total_weighted_landing_price"]
        .isna()
        .sum()
    )


    # ======================================
    # 12. REMOVE INVALID ESSENTIAL RECORDS
    # ======================================

    before = len(df)

    df = df.dropna(
        subset=[
            "date_",
            "product_id",
            "procured_quantity",
            "unit_selling_price"
        ]
    )

    removed = before - len(df)

    total_removed_rows += removed


    # ======================================
    # 13. REMOVE EXACT DUPLICATES
    # ======================================

    df = df.drop_duplicates()


    # ======================================
    # 14. WRITE CLEANED DATA
    # ======================================

    df.to_csv(
        output_file,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False

    output_rows = len(df)
    total_output_rows += output_rows


    print(
        f"Chunk {chunk_number}: "
        f"Input={input_rows:,} | "
        f"Output={output_rows:,} | "
        f"Removed={removed:,}"
    )


# ==========================================
# 15. FINAL REPORT
# ==========================================

print("\n" + "=" * 60)
print("CLEANING COMPLETED")
print("=" * 60)

print(
    f"\nTotal input rows: "
    f"{total_input_rows:,}"
)

print(
    f"Total output rows: "
    f"{total_output_rows:,}"
)

print(
    f"Rows removed: "
    f"{total_removed_rows:,}"
)

print(
    f"Missing landing price values: "
    f"{total_missing_landing_price:,}"
)

print(
    f"\nCleaned file created at:"
)

print(output_file)

print("\n" + "=" * 60)
print("DONE!")
print("=" * 60)