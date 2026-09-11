import pandas as pd
from pathlib import Path

# ============================================================
# STEP 11: NUMERICAL VALUE VALIDATION
# ============================================================

project_root = Path(__file__).parent.parent

input_file = (
    project_root
    / "dataset"
    / "processed"
    / "sales_product_master_imputed.csv"
)

chunk_size = 500_000

print("=" * 60)
print("NUMERICAL VALUE VALIDATION")
print("=" * 60)

print(f"\nInput file:")
print(input_file)


# ------------------------------------------------------------
# Counters
# ------------------------------------------------------------

total_rows = 0

quantity_negative = 0
quantity_zero = 0
quantity_missing = 0

selling_negative = 0
selling_zero = 0
selling_missing = 0

discount_negative = 0
discount_zero = 0
discount_missing = 0

landing_negative = 0
landing_zero = 0
landing_missing = 0


# Extreme values
quantity_extreme = 0
selling_extreme = 0
discount_extreme = 0
landing_extreme = 0


# ------------------------------------------------------------
# PASS 1: Basic validation
# ------------------------------------------------------------

print("\nChecking numerical columns...")

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_file,
        usecols=[
            "procured_quantity",
            "unit_selling_price",
            "total_discount_amount",
            "total_weighted_landing_price"
        ],
        chunksize=chunk_size
    ),
    start=1
):

    total_rows += len(chunk)

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    quantity = chunk["procured_quantity"]

    quantity_negative += (quantity < 0).sum()
    quantity_zero += (quantity == 0).sum()
    quantity_missing += quantity.isna().sum()

    # Extreme quantity:
    # Values greater than 1000 units per transaction
    quantity_extreme += (quantity > 1000).sum()

    # --------------------------------------------------------
    # Selling price
    # --------------------------------------------------------

    selling = chunk["unit_selling_price"]

    selling_negative += (selling < 0).sum()
    selling_zero += (selling == 0).sum()
    selling_missing += selling.isna().sum()

    # Extreme selling price:
    # Values greater than ₹10,000 per unit
    selling_extreme += (selling > 10000).sum()

    # --------------------------------------------------------
    # Discount
    # --------------------------------------------------------

    discount = chunk["total_discount_amount"]

    discount_negative += (discount < 0).sum()
    discount_zero += (discount == 0).sum()
    discount_missing += discount.isna().sum()

    # Extreme discount:
    # Values greater than ₹10,000
    discount_extreme += (discount > 10000).sum()

    # --------------------------------------------------------
    # Landing price
    # --------------------------------------------------------

    landing = chunk["total_weighted_landing_price"]

    landing_negative += (landing < 0).sum()
    landing_zero += (landing == 0).sum()
    landing_missing += landing.isna().sum()

    # Extreme landing price:
    # Values greater than ₹10,000
    landing_extreme += (landing > 10000).sum()

    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


# ============================================================
# FINAL REPORT
# ============================================================

print("\n" + "=" * 60)
print("NUMERICAL VALIDATION RESULTS")
print("=" * 60)

print("\nPROCURED QUANTITY")
print("-" * 40)
print(f"Negative values : {quantity_negative:,}")
print(f"Zero values     : {quantity_zero:,}")
print(f"Missing values  : {quantity_missing:,}")
print(f"> 1000 units    : {quantity_extreme:,}")

print("\nUNIT SELLING PRICE")
print("-" * 40)
print(f"Negative values : {selling_negative:,}")
print(f"Zero values     : {selling_zero:,}")
print(f"Missing values  : {selling_missing:,}")
print(f"> ₹10,000       : {selling_extreme:,}")

print("\nTOTAL DISCOUNT AMOUNT")
print("-" * 40)
print(f"Negative values : {discount_negative:,}")
print(f"Zero values     : {discount_zero:,}")
print(f"Missing values  : {discount_missing:,}")
print(f"> ₹10,000       : {discount_extreme:,}")

print("\nTOTAL WEIGHTED LANDING PRICE")
print("-" * 40)
print(f"Negative values : {landing_negative:,}")
print(f"Zero values     : {landing_zero:,}")
print(f"Missing values  : {landing_missing:,}")
print(f"> ₹10,000       : {landing_extreme:,}")


print("\n" + "=" * 60)
print("TOTAL ROWS VALIDATED")
print("=" * 60)

print(f"Total rows: {total_rows:,}")

print("\n" + "=" * 60)
print("STEP 11 ANALYSIS COMPLETED")
print("=" * 60)