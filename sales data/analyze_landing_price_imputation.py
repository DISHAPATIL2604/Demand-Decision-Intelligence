import pandas as pd
from pathlib import Path

# ============================================================
# STEP 10: LANDING PRICE IMPUTATION ANALYSIS
# ============================================================

project_root = Path(__file__).parent.parent

input_file = (
    project_root
    / "dataset"
    / "cleaned"
    / "sales_product_master.csv"
)

print("=" * 60)
print("LANDING PRICE IMPUTATION ANALYSIS")
print("=" * 60)

print(f"\nInput file:")
print(input_file)

# ------------------------------------------------------------
# Step 1: Find valid landing-price statistics per product
# ------------------------------------------------------------

print("\nCalculating product-wise landing price statistics...")

product_stats = {}

total_rows = 0
missing_rows = 0

chunk_size = 500_000

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

    missing_rows += (
        chunk["total_weighted_landing_price"].isna()
    ).sum()

    valid = chunk.dropna(
        subset=["total_weighted_landing_price"]
    )

    grouped = valid.groupby("product_id")[
        "total_weighted_landing_price"
    ].agg(
        valid_count="count",
        median="median"
    )

    for product_id, row in grouped.iterrows():

        if product_id not in product_stats:

            product_stats[product_id] = {
                "valid_count": int(row["valid_count"]),
                "median": float(row["median"])
            }

        else:

            # For the analysis we need the total valid count.
            # Median is kept from the first accumulated group
            # and will be recalculated in the second pass.
            product_stats[product_id]["valid_count"] += int(
                row["valid_count"]
            )

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


# ------------------------------------------------------------
# Step 2: Determine how many missing rows have
#         product-level valid prices
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("PRODUCT-LEVEL COVERAGE")
print("=" * 60)

products_with_valid_price = 0
products_without_valid_price = 0

# We only need the product IDs that have missing landing price.
missing_product_ids = set()

for chunk in pd.read_csv(
    input_file,
    usecols=[
        "product_id",
        "total_weighted_landing_price"
    ],
    chunksize=chunk_size
):

    missing = chunk[
        chunk["total_weighted_landing_price"].isna()
    ]

    missing_product_ids.update(
        missing["product_id"].dropna().unique()
    )


for product_id in missing_product_ids:

    if product_id in product_stats:

        products_with_valid_price += 1

    else:

        products_without_valid_price += 1


print(
    f"\nUnique products with missing landing price: "
    f"{len(missing_product_ids):,}"
)

print(
    f"Products having valid historical landing price: "
    f"{products_with_valid_price:,}"
)

print(
    f"Products having NO valid landing price: "
    f"{products_without_valid_price:,}"
)


# ------------------------------------------------------------
# Step 3: Count missing sales rows that can potentially
#         use product-level information
# ------------------------------------------------------------

fillable_rows = 0
non_fillable_rows = 0

for chunk in pd.read_csv(
    input_file,
    usecols=[
        "product_id",
        "total_weighted_landing_price"
    ],
    chunksize=chunk_size
):

    missing = chunk[
        "total_weighted_landing_price"
    ].isna()

    missing_data = chunk.loc[
        missing,
        "product_id"
    ]

    for product_id in missing_data:

        if product_id in product_stats:
            fillable_rows += 1
        else:
            non_fillable_rows += 1


# ------------------------------------------------------------
# FINAL REPORT
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("FINAL IMPUTATION ANALYSIS")
print("=" * 60)

print(
    f"\nTotal rows: "
    f"{total_rows:,}"
)

print(
    f"Missing landing price rows: "
    f"{missing_rows:,}"
)

print(
    f"Potentially fillable using product history: "
    f"{fillable_rows:,}"
)

print(
    f"Without product-level price history: "
    f"{non_fillable_rows:,}"
)

if missing_rows > 0:

    fillable_percentage = (
        fillable_rows / missing_rows
    ) * 100

    non_fillable_percentage = (
        non_fillable_rows / missing_rows
    ) * 100

    print(
        f"\nPotentially fillable: "
        f"{fillable_percentage:.2f}%"
    )

    print(
        f"Not fillable at product level: "
        f"{non_fillable_percentage:.2f}%"
    )


print("\n" + "=" * 60)
print("STEP 10 ANALYSIS COMPLETED")
print("=" * 60)