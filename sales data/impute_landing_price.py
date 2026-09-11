import pandas as pd
from pathlib import Path

# ============================================================
# STEP 10B: LANDING PRICE IMPUTATION
# ============================================================

project_root = Path(__file__).parent.parent

input_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_product_master.csv"
)

output_dir = (
    project_root
    / "dataset"
    / "processed"
)

output_file = (
    output_dir
    / "sales_product_master_imputed.csv"
)

output_dir.mkdir(parents=True, exist_ok=True)

chunk_size = 500_000

print("=" * 60)
print("LANDING PRICE IMPUTATION")
print("=" * 60)

print(f"\nInput:")
print(input_file)

print(f"\nOutput:")
print(output_file)


# ============================================================
# PASS 1
# Calculate product-wise median landing price
# ============================================================

print("\n" + "=" * 60)
print("PASS 1: CALCULATING PRODUCT-WISE MEDIANS")
print("=" * 60)

# Store valid landing prices for each product.
# There are only ~17k products in sales, so this remains manageable.
product_prices = {}

total_rows = 0
missing_before = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_file,
        usecols=[
            "product_id",
            "total_weighted_landing_price"
        ],
        chunksize=chunk_size
    ),
    start=1
):

    total_rows += len(chunk)

    missing_before += (
        chunk["total_weighted_landing_price"].isna()
    ).sum()

    valid = chunk.dropna(
        subset=["total_weighted_landing_price"]
    )

    for product_id, prices in valid.groupby("product_id")[
        "total_weighted_landing_price"
    ]:

        if product_id not in product_prices:
            product_prices[product_id] = []

        product_prices[product_id].extend(
            prices.tolist()
        )

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


print("\nCalculating medians...")

product_medians = {}

for product_id, prices in product_prices.items():

    product_medians[product_id] = pd.Series(
        prices
    ).median()


print(
    f"Products with valid landing price: "
    f"{len(product_medians):,}"
)


# ============================================================
# PASS 2
# Impute missing values
# ============================================================

print("\n" + "=" * 60)
print("PASS 2: IMPUTING MISSING VALUES")
print("=" * 60)

# Remove old output if it exists
if output_file.exists():
    output_file.unlink()

total_output_rows = 0
imputed_rows = 0
remaining_missing = 0

first_chunk = True

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_file,
        chunksize=chunk_size
    ),
    start=1
):

    missing_mask = (
        chunk["total_weighted_landing_price"].isna()
    )

    missing_product_ids = chunk.loc[
        missing_mask,
        "product_id"
    ]

    # Map product_id → historical median
    replacement_values = missing_product_ids.map(
        product_medians
    )

    # Only fill where a product-level median exists
    can_impute = (
        missing_mask
        & replacement_values.notna()
    )

    chunk.loc[
        can_impute,
        "total_weighted_landing_price"
    ] = replacement_values[can_impute]

    current_imputed = can_impute.sum()

    current_remaining = (
        chunk["total_weighted_landing_price"]
        .isna()
        .sum()
    )

    imputed_rows += current_imputed
    remaining_missing += current_remaining
    total_output_rows += len(chunk)

    chunk.to_csv(
        output_file,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False
    )

    first_chunk = False

    print(
        f"Chunk {chunk_number}: "
        f"Rows={len(chunk):,} | "
        f"Imputed={current_imputed:,}"
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("IMPUTATION COMPLETED")
print("=" * 60)

print(
    f"\nOriginal rows: "
    f"{total_rows:,}"
)

print(
    f"Output rows: "
    f"{total_output_rows:,}"
)

print(
    f"Missing before imputation: "
    f"{missing_before:,}"
)

print(
    f"Rows imputed: "
    f"{imputed_rows:,}"
)

print(
    f"Missing remaining: "
    f"{remaining_missing:,}"
)

print(
    f"\nOutput file created at:"
)

print(output_file)

print("\n" + "=" * 60)
print("STEP 10B COMPLETED")
print("=" * 60)