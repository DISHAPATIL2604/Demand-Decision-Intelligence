import pandas as pd
from pathlib import Path

# ============================================================
# STEP 12: DUPLICATE TRANSACTION VALIDATION
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
print("DUPLICATE TRANSACTION VALIDATION")
print("=" * 60)

print(f"\nInput file:")
print(input_file)


# ------------------------------------------------------------
# Counters
# ------------------------------------------------------------

total_rows = 0

# We use sets of transaction keys.
# Only unique keys are stored, not the complete dataset.

order_product_keys = set()
order_cart_product_keys = set()

duplicate_order_product = 0
duplicate_order_cart_product = 0

# Samples only
duplicate_samples = []


# ------------------------------------------------------------
# Process chunks
# ------------------------------------------------------------

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_file,
        usecols=[
            "date_",
            "order_id",
            "cart_id",
            "product_id",
            "procured_quantity",
            "unit_selling_price"
        ],
        chunksize=chunk_size
    ),
    start=1
):

    total_rows += len(chunk)

    # --------------------------------------------------------
    # Key 1:
    # date + order + product
    # --------------------------------------------------------

    keys_1 = list(
        zip(
            chunk["date_"],
            chunk["order_id"],
            chunk["product_id"]
        )
    )

    for i, key in enumerate(keys_1):

        if key in order_product_keys:

            duplicate_order_product += 1

            if len(duplicate_samples) < 10:

                duplicate_samples.append(
                    (
                        "date + order_id + product_id",
                        chunk.iloc[i].to_dict()
                    )
                )

        else:

            order_product_keys.add(key)


    # --------------------------------------------------------
    # Key 2:
    # date + order + cart + product
    # --------------------------------------------------------

    keys_2 = list(
        zip(
            chunk["date_"],
            chunk["order_id"],
            chunk["cart_id"],
            chunk["product_id"]
        )
    )

    for key in keys_2:

        if key in order_cart_product_keys:

            duplicate_order_cart_product += 1

        else:

            order_cart_product_keys.add(key)


    print(
        f"Chunk {chunk_number}: "
        f"{total_rows:,} rows processed"
    )


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 60)
print("DUPLICATE VALIDATION RESULTS")
print("=" * 60)

print(f"\nTotal rows checked: {total_rows:,}")

print(
    "\nDuplicate rows based on:"
    "\n(date + order_id + product_id)"
)

print(
    f"Duplicates found: "
    f"{duplicate_order_product:,}"
)

print(
    "\nDuplicate rows based on:"
    "\n(date + order_id + cart_id + product_id)"
)

print(
    f"Duplicates found: "
    f"{duplicate_order_cart_product:,}"
)


# ============================================================
# SAMPLE DUPLICATES
# ============================================================

print("\n" + "=" * 60)
print("DUPLICATE SAMPLES")
print("=" * 60)

if not duplicate_samples:

    print("\nNo duplicates found.")

else:

    for number, (key_type, row) in enumerate(
        duplicate_samples,
        start=1
    ):

        print(f"\nExample {number}")
        print(f"Key: {key_type}")

        print(
            f"date={row['date_']}, "
            f"order_id={row['order_id']}, "
            f"cart_id={row['cart_id']}, "
            f"product_id={row['product_id']}, "
            f"quantity={row['procured_quantity']}, "
            f"selling_price={row['unit_selling_price']}"
        )


print("\n" + "=" * 60)
print("STEP 12 ANALYSIS COMPLETED")
print("=" * 60)