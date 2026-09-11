import pandas as pd
from pathlib import Path

# ============================================================
# STEP 11A: INVESTIGATE SUSPICIOUS NUMERICAL VALUES
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
print("NUMERICAL ANOMALY INVESTIGATION")
print("=" * 60)

# Counters
quantity_zero = 0
selling_zero = 0
landing_zero = 0

selling_high = 0
landing_high = 0

# Samples only — no output file
quantity_zero_samples = []
selling_zero_samples = []
landing_zero_samples = []
selling_high_samples = []
landing_high_samples = []

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_file,
        usecols=[
            "date_",
            "city_name",
            "order_id",
            "procured_quantity",
            "unit_selling_price",
            "total_discount_amount",
            "product_id",
            "product_name",
            "total_weighted_landing_price"
        ],
        chunksize=chunk_size
    ),
    start=1
):

    # --------------------------------------------------------
    # Zero quantity
    # --------------------------------------------------------

    mask = chunk["procured_quantity"] == 0
    quantity_zero += mask.sum()

    if len(quantity_zero_samples) < 10:
        quantity_zero_samples.extend(
            chunk.loc[mask].head(
                10 - len(quantity_zero_samples)
            ).to_dict("records")
        )

    # --------------------------------------------------------
    # Zero selling price
    # --------------------------------------------------------

    mask = chunk["unit_selling_price"] == 0
    selling_zero += mask.sum()

    if len(selling_zero_samples) < 10:
        selling_zero_samples.extend(
            chunk.loc[mask].head(
                10 - len(selling_zero_samples)
            ).to_dict("records")
        )

    # --------------------------------------------------------
    # Zero landing price
    # --------------------------------------------------------

    mask = chunk["total_weighted_landing_price"] == 0
    landing_zero += mask.sum()

    if len(landing_zero_samples) < 10:
        landing_zero_samples.extend(
            chunk.loc[mask].head(
                10 - len(landing_zero_samples)
            ).to_dict("records")
        )

    # --------------------------------------------------------
    # High selling price
    # --------------------------------------------------------

    mask = chunk["unit_selling_price"] > 10000
    selling_high += mask.sum()

    if len(selling_high_samples) < 10:
        selling_high_samples.extend(
            chunk.loc[mask].head(
                10 - len(selling_high_samples)
            ).to_dict("records")
        )

    # --------------------------------------------------------
    # High landing price
    # --------------------------------------------------------

    mask = chunk["total_weighted_landing_price"] > 10000
    landing_high += mask.sum()

    if len(landing_high_samples) < 10:
        landing_high_samples.extend(
            chunk.loc[mask].head(
                10 - len(landing_high_samples)
            ).to_dict("records")
        )

    print(
        f"Chunk {chunk_number}: "
        f"{len(chunk):,} rows checked"
    )


# ============================================================
# RESULTS
# ============================================================

def print_samples(title, samples):
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)

    if not samples:
        print("No examples found.")
        return

    for i, row in enumerate(samples, start=1):
        print(
            f"\nExample {i}: "
            f"date={row['date_']}, "
            f"city={row['city_name']}, "
            f"product_id={row['product_id']}, "
            f"product={row['product_name']}, "
            f"quantity={row['procured_quantity']}, "
            f"selling_price={row['unit_selling_price']}, "
            f"discount={row['total_discount_amount']}, "
            f"landing_price={row['total_weighted_landing_price']}"
        )


print("\n" + "=" * 60)
print("COUNTS")
print("=" * 60)

print(f"\nZero quantity       : {quantity_zero:,}")
print(f"Zero selling price  : {selling_zero:,}")
print(f"Zero landing price  : {landing_zero:,}")
print(f"Selling price > ₹10,000 : {selling_high:,}")
print(f"Landing price > ₹10,000 : {landing_high:,}")


print_samples(
    "ZERO QUANTITY — SAMPLE",
    quantity_zero_samples
)

print_samples(
    "ZERO SELLING PRICE — SAMPLE",
    selling_zero_samples
)

print_samples(
    "ZERO LANDING PRICE — SAMPLE",
    landing_zero_samples
)

print_samples(
    "HIGH SELLING PRICE — SAMPLE",
    selling_high_samples
)

print_samples(
    "HIGH LANDING PRICE — SAMPLE",
    landing_high_samples
)


print("\n" + "=" * 60)
print("STEP 11A COMPLETED")
print("=" * 60)