import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal, engine
from backend.models.product import Product

PRODUCT_FILE = BASE_DIR / "dataset" / "raw" / "products" / "dim_product.csv"

def clean_value(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value == "" else value

def to_int(value):
    val = clean_value(value)
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def load_products(batch_size: int = 3000):
    if not PRODUCT_FILE.exists():
        raise FileNotFoundError(f"Product master not found: {PRODUCT_FILE}")

    print(f"Reading product master from {PRODUCT_FILE}...")
    db: Session = SessionLocal()
    
    total_processed = 0
    records = {}
    
    try:
        with open(PRODUCT_FILE, "r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                p_id = to_int(row.get("product_id"))
                p_name = clean_value(row.get("product_name"))
                if p_id is None or p_name is None:
                    continue

                record = {
                    "product_id": p_id,
                    "product_name": p_name,
                    "unit": clean_value(row.get("unit")),
                    "product_type": clean_value(row.get("product_type")),
                    "brand_name": clean_value(row.get("brand_name")),
                    "manufacturer_name": clean_value(row.get("manufacturer_name")),
                    "l0_category": clean_value(row.get("l0_category")),
                    "l1_category": clean_value(row.get("l1_category")),
                    "l2_category": clean_value(row.get("l2_category")),
                    "l0_category_id": to_int(row.get("l0_category_id")),
                    "l1_category_id": to_int(row.get("l1_category_id")),
                    "l2_category_id": to_int(row.get("l2_category_id")),
                    "is_active": True,
                }
                records[p_id] = record

                if len(records) >= batch_size:
                    batch_list = list(records.values())
                    _upsert_batch(db, batch_list)
                    total_processed += len(batch_list)
                    print(f"Processed {total_processed} products...")
                    records.clear()

            if records:
                batch_list = list(records.values())
                _upsert_batch(db, batch_list)
                total_processed += len(batch_list)
                records.clear()

        print(f"\nSuccessfully loaded {total_processed} products into PostgreSQL.")
    except Exception as e:
        db.rollback()
        print(f"Error loading products: {e}")
        raise
    finally:
        db.close()

def _upsert_batch(db: Session, batch):
    stmt = insert(Product).values(batch)
    update_dict = {
        col.name: col
        for col in stmt.excluded
        if col.name not in ("product_id", "created_at")
    }
    stmt = stmt.on_conflict_do_update(
        index_elements=[Product.product_id],
        set_=update_dict
    )
    db.execute(stmt)
    db.commit()

if __name__ == "__main__":
    load_products()