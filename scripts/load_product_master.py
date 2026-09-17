import csv
from pathlib import Path

from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.models.product import Product


BASE_DIR = Path(__file__).resolve().parent.parent

PRODUCT_FILE = (
    BASE_DIR
    / "dataset"
    / "raw"
    / "products"
    / "dim_product.csv"
)


def clean_value(value):
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    return value


def to_int(value):
    value = clean_value(value)

    if value is None:
        return None

    return int(float(value))


def load_products():
    if not PRODUCT_FILE.exists():
        raise FileNotFoundError(
            f"Product master not found: {PRODUCT_FILE}"
        )

    db: Session = SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        with open(
            PRODUCT_FILE,
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            required_columns = {
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
                "l2_category_id",
            }

            missing = required_columns - set(reader.fieldnames or [])

            if missing:
                raise ValueError(
                    f"Missing product columns: {sorted(missing)}"
                )

            for row in reader:

                try:
                    product_id = to_int(row["product_id"])
                    product_name = clean_value(row["product_name"])

                    if product_id is None or product_name is None:
                        skipped += 1
                        continue

                    product = (
                        db.query(Product)
                        .filter(Product.product_id == product_id)
                        .first()
                    )

                    if product is None:

                        product = Product(
                            product_id=product_id,
                            product_name=product_name,
                            unit=clean_value(row["unit"]),
                            product_type=clean_value(row["product_type"]),
                            brand_name=clean_value(row["brand_name"]),
                            manufacturer_name=clean_value(
                                row["manufacturer_name"]
                            ),
                            l0_category=clean_value(row["l0_category"]),
                            l1_category=clean_value(row["l1_category"]),
                            l2_category=clean_value(row["l2_category"]),
                            l0_category_id=to_int(
                                row["l0_category_id"]
                            ),
                            l1_category_id=to_int(
                                row["l1_category_id"]
                            ),
                            l2_category_id=to_int(
                                row["l2_category_id"]
                            ),
                            is_active=True,
                        )

                        db.add(product)
                        inserted += 1

                    else:

                        product.product_name = product_name
                        product.unit = clean_value(row["unit"])
                        product.product_type = clean_value(
                            row["product_type"]
                        )
                        product.brand_name = clean_value(
                            row["brand_name"]
                        )
                        product.manufacturer_name = clean_value(
                            row["manufacturer_name"]
                        )
                        product.l0_category = clean_value(
                            row["l0_category"]
                        )
                        product.l1_category = clean_value(
                            row["l1_category"]
                        )
                        product.l2_category = clean_value(
                            row["l2_category"]
                        )
                        product.l0_category_id = to_int(
                            row["l0_category_id"]
                        )
                        product.l1_category_id = to_int(
                            row["l1_category_id"]
                        )
                        product.l2_category_id = to_int(
                            row["l2_category_id"]
                        )
                        product.is_active = True

                        updated += 1

                except Exception as row_error:
                    print(f"Skipping product row: {row_error}")
                    skipped += 1

            db.commit()

            print("\nProduct master loading completed.")
            print(f"Inserted : {inserted}")
            print(f"Updated  : {updated}")
            print(f"Skipped  : {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    load_products()