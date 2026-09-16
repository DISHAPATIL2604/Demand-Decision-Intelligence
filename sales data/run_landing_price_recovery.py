import duckdb
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sales_master = project_root / "dataset" / "cleaned" / "sales_product_master.csv"
reports_dir = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)
processed_dir = project_root / "dataset" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("PHASE 2: DETERMINISTIC LANDING PRICE RECOVERY AUDIT")
print("=" * 70)

con = duckdb.connect()

# 1. Total rows and missing landing price
print("\n1. Querying missing landing price rows...")
missing_summary = con.execute(f"""
    SELECT 
        COUNT(*) as total_sales_rows,
        COUNT(total_weighted_landing_price) as non_missing_lp_rows,
        COUNT(*) - COUNT(total_weighted_landing_price) as missing_lp_rows,
        COUNT(DISTINCT product_id) as total_products,
        COUNT(DISTINCT CASE WHEN total_weighted_landing_price IS NULL THEN product_id END) as products_with_missing_lp
    FROM read_csv_auto('{sales_master.as_posix()}', sample_size=100000)
""").df()
print(missing_summary.to_string(index=False))

# 2. Compute historical product-city and product-only medians for affected products
print("\n2. Computing deterministic historical landing prices (Tier 1 & Tier 2)...")
lp_recovery_query = f"""
    WITH valid_lp AS (
        SELECT 
            product_id,
            city_name,
            total_weighted_landing_price
        FROM read_csv_auto('{sales_master.as_posix()}', sample_size=100000)
        WHERE total_weighted_landing_price IS NOT NULL
    ),
    prod_city_medians AS (
        SELECT 
            product_id,
            city_name,
            MEDIAN(total_weighted_landing_price) as median_lp_prod_city,
            COUNT(*) as valid_samples_prod_city
        FROM valid_lp
        GROUP BY product_id, city_name
    ),
    prod_medians AS (
        SELECT 
            product_id,
            MEDIAN(total_weighted_landing_price) as median_lp_prod,
            COUNT(*) as valid_samples_prod
        FROM valid_lp
        GROUP BY product_id
    ),
    missing_rows AS (
        SELECT 
            product_id,
            city_name,
            COUNT(*) as missing_count
        FROM read_csv_auto('{sales_master.as_posix()}', sample_size=100000)
        WHERE total_weighted_landing_price IS NULL
        GROUP BY product_id, city_name
    )
    SELECT 
        m.product_id,
        m.city_name,
        m.missing_count,
        pcm.median_lp_prod_city,
        pcm.valid_samples_prod_city,
        pm.median_lp_prod,
        pm.valid_samples_prod,
        CASE 
            WHEN pcm.median_lp_prod_city IS NOT NULL THEN 'Tier_1_Product_City_Median'
            WHEN pm.median_lp_prod IS NOT NULL THEN 'Tier_2_Product_Median'
            ELSE 'UNRESOLVED_NO_HISTORY'
        END as recovery_tier,
        CASE 
            WHEN pcm.median_lp_prod_city IS NOT NULL THEN pcm.median_lp_prod_city
            WHEN pm.median_lp_prod IS NOT NULL THEN pm.median_lp_prod
            ELSE NULL
        END as recovered_landing_price
    FROM missing_rows m
    LEFT JOIN prod_city_medians pcm ON m.product_id = pcm.product_id AND m.city_name = pcm.city_name
    LEFT JOIN prod_medians pm ON m.product_id = pm.product_id
"""

df_recovery = con.execute(lp_recovery_query).df()

# Summary by tier
tier_summary = df_recovery.groupby("recovery_tier").agg(
    unique_products=("product_id", "nunique"),
    missing_rows=("missing_count", "sum")
).reset_index()

print("\nRecovery Tier Breakdown:")
print(tier_summary.to_string(index=False))

# Save recovery lookup table
output_audit_csv = reports_dir / "landing_price_recovery_audit.csv"
df_recovery.to_csv(output_audit_csv, index=False)
print(f"\nAudit detail saved to: {output_audit_csv}")

lookup_table_csv = processed_dir / "landing_price_recovery_lookup.csv"
df_recovery.to_csv(lookup_table_csv, index=False)
print(f"Recovery lookup saved to: {lookup_table_csv}")

# 3. Unresolved Products Detail
unresolved = df_recovery[df_recovery["recovery_tier"] == "UNRESOLVED_NO_HISTORY"]
unresolved_summary = unresolved.groupby("product_id")["missing_count"].sum().reset_index()
print(f"\nUnresolved Products (count={len(unresolved_summary)}):")
print(unresolved_summary.sort_values(by="missing_count", ascending=False).to_string(index=False))

# 4. Validations
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
tot_missing = df_recovery["missing_count"].sum()
recovered_tier1 = df_recovery[df_recovery["recovery_tier"] == "Tier_1_Product_City_Median"]["missing_count"].sum()
recovered_tier2 = df_recovery[df_recovery["recovery_tier"] == "Tier_2_Product_Median"]["missing_count"].sum()
tot_recovered = recovered_tier1 + recovered_tier2
tot_unresolved = df_recovery[df_recovery["recovery_tier"] == "UNRESOLVED_NO_HISTORY"]["missing_count"].sum()

print(f"Total Missing Rows              : {tot_missing:,} (Expected: 79,355)")
print(f"Tier 1 (Same Product + City)    : {recovered_tier1:,} (Expected: 28,171)")
print(f"Tier 2 (Same Product Cross-City): {recovered_tier2:,} (Expected: 9,313)")
print(f"Total Recoverable Rows          : {tot_recovered:,} (Expected: 37,484)")
print(f"Total Unresolved Rows           : {tot_unresolved:,} (Expected: 41,871)")

assert tot_missing == 79355, f"Expected 79,355 missing rows, got {tot_missing}"
assert recovered_tier1 == 28171, f"Expected 28,171 Tier 1 rows, got {recovered_tier1}"
assert recovered_tier2 == 9313, f"Expected 9,313 Tier 2 rows, got {recovered_tier2}"
assert tot_recovered == 37484, f"Expected 37,484 recovered rows, got {tot_recovered}"
assert tot_unresolved == 41871, f"Expected 41,871 unresolved rows, got {tot_unresolved}"
print("\n>>> ALL LANDING PRICE VALIDATION CHECKS PASSED (EXACT MATCH) <<<")
con.close()
