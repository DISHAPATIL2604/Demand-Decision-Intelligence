import os
import time
import duckdb
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sales_master = project_root / "dataset" / "cleaned" / "sales_product_master.csv"
temp_output = project_root / "dataset" / "cleaned" / "sales_product_master_clean_temp.csv"
lp_lookup = project_root / "dataset" / "processed" / "landing_price_recovery_lookup.csv"
reports_dir = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

print("=" * 75)
print("FINAL DATA CLEANING: MATERIALIZING CANONICAL SALES MASTER")
print("=" * 75)

t0 = time.time()
con = duckdb.connect()

print("\n1. Joining deterministic landing price recovery into sales master...")
print(f"Source Sales Master : {sales_master}")
print(f"Recovery Lookup     : {lp_lookup}")
print(f"Temporary Target    : {temp_output}")

export_query = f"""
COPY (
    SELECT 
        s.date_,
        s.city_name,
        s.order_id,
        s.cart_id,
        s.dim_customer_key,
        s.procured_quantity,
        s.unit_selling_price,
        s.total_discount_amount,
        s.product_id,
        COALESCE(s.total_weighted_landing_price, r.recovered_landing_price) AS total_weighted_landing_price,
        CASE 
            WHEN s.total_weighted_landing_price IS NOT NULL THEN 'original'
            WHEN r.recovery_tier IS NOT NULL THEN r.recovery_tier
            ELSE 'UNRESOLVED_NO_HISTORY'
        END AS price_fill_method,
        s.product_name,
        s.unit,
        s.product_type,
        s.brand_name,
        s.manufacturer_name,
        s.l0_category,
        s.l1_category,
        s.l2_category,
        s.l0_category_id,
        s.l1_category_id,
        s.l2_category_id
    FROM read_csv_auto('{sales_master.as_posix()}') s
    LEFT JOIN read_csv_auto('{lp_lookup.as_posix()}') r
        ON s.product_id = r.product_id AND s.city_name = r.city_name
) TO '{temp_output.as_posix()}' (HEADER, DELIMITER ',');
"""

print("\nExecuting stream export via DuckDB...")
con.execute(export_query)
print(f"Export completed in {time.time() - t0:.2f}s!")

# ============================================================
# RIGOROUS POST-GENERATION VALIDATION
# ============================================================
print("\n" + "=" * 75)
print("VALIDATING MATERIALIZED CLEAN SALES MASTER")
print("=" * 75)

val_query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(date_) as non_null_dates,
    MIN(date_) as min_date,
    MAX(date_) as max_date,
    COUNT(DISTINCT date_) as unique_dates,
    COUNT(DISTINCT product_id) as unique_products,
    COUNT(DISTINCT city_name) as unique_cities,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_gross_revenue,
    COUNT(*) - COUNT(total_weighted_landing_price) as missing_lp_rows,
    COUNT(CASE WHEN price_fill_method = 'original' THEN 1 END) as lp_original_count,
    COUNT(CASE WHEN price_fill_method = 'Tier_1_Product_City_Median' THEN 1 END) as lp_tier1_recovered,
    COUNT(CASE WHEN price_fill_method = 'Tier_2_Product_Median' THEN 1 END) as lp_tier2_recovered,
    COUNT(CASE WHEN price_fill_method = 'UNRESOLVED_NO_HISTORY' THEN 1 END) as lp_unresolved_count,
    COUNT(*) - COUNT(product_name) as missing_product_names,
    COUNT(*) - COUNT(brand_name) as missing_brands,
    COUNT(*) - COUNT(manufacturer_name) as missing_manufacturers
FROM read_csv_auto('{temp_output.as_posix()}')
"""

val_df = con.execute(val_query).df()
print("\nValidation Summary:")
print(val_df.to_string(index=False))

# Assertions
total_rows = int(val_df["total_rows"][0])
missing_lp = int(val_df["missing_lp_rows"][0])
lp_tier1 = int(val_df["lp_tier1_recovered"][0])
lp_tier2 = int(val_df["lp_tier2_recovered"][0])
lp_unresolved = int(val_df["lp_unresolved_count"][0])
missing_names = int(val_df["missing_product_names"][0])

assert total_rows == 46706387, f"Row count mismatch! Expected 46,706,387, got {total_rows}"
assert missing_lp == 41871, f"Missing landing price mismatch! Expected 41,871, got {missing_lp}"
assert lp_tier1 == 28171, f"Tier 1 mismatch! Expected 28,171, got {lp_tier1}"
assert lp_tier2 == 9313, f"Tier 2 mismatch! Expected 9,313, got {lp_tier2}"
assert lp_unresolved == 41871, f"Unresolved mismatch! Expected 41,871, got {lp_unresolved}"
assert missing_names == 532122, f"Missing product names mismatch! Expected 532,122, got {missing_names}"

print("\n>>> ALL 6 RIGOROUS ASSERTIONS PASSED WITH 100% INTEGRITY <<<")

con.close()

# Safely replace old sales_product_master.csv with the new validated file
print(f"\nReplacing {sales_master.name} with validated clean master...")
if os.path.exists(sales_master):
    os.remove(sales_master)
os.rename(temp_output, sales_master)

print(f"\nFINAL CLEAN DATASET IS READY AT: {sales_master}")
print(f"Total time elapsed: {time.time() - t0:.2f}s")
print("=" * 75)
