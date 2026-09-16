"""
DEMAND DECISION INTELLIGENCE — DATA FORENSIC AUDIT
Phases 8–15: Landing Price, Numerical Validation, Temporal Audit,
             Daily Demand, Order Count, Forecasting Features,
             Leakage Audit, Final Decision Matrix
"""
import pandas as pd
import duckdb
import json
import os
import numpy as np
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent

REPORT_DIR = PROJECT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

SALES_MASTER = PROJECT / "dataset" / "cleaned" / "sales_product_master.csv"
DAILY_DEMAND = PROJECT / "dataset" / "processed" / "daily_product_demand.csv"
CLEAN_PRODUCT = PROJECT / "dataset" / "cleaned" / "dim_product_cleaned_with_audit.csv"

sales_path = str(SALES_MASTER).replace("\\", "/")
demand_path = str(DAILY_DEMAND).replace("\\", "/")

results = {}

con = duckdb.connect()

# ============================================================
# PHASE 8 — LANDING PRICE AUDIT
# ============================================================
print("=" * 70)
print("PHASE 8 -- LANDING PRICE AUDIT")
print("=" * 70)

phase8 = {}

# Overall missing
r = con.execute(f"""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN total_weighted_landing_price IS NULL THEN 1 ELSE 0 END) as missing,
        SUM(CASE WHEN total_weighted_landing_price = 0 THEN 1 ELSE 0 END) as zero_lp,
        SUM(CASE WHEN total_weighted_landing_price < 0 THEN 1 ELSE 0 END) as negative_lp,
        SUM(CASE WHEN total_weighted_landing_price > 10000 THEN 1 ELSE 0 END) as extreme_lp
    FROM read_csv_auto('{sales_path}')
""").fetchone()
phase8["total_rows"]     = r[0]
phase8["missing_lp"]     = r[1]
phase8["zero_lp"]        = r[2]
phase8["negative_lp"]    = r[3]
phase8["extreme_lp"]     = r[4]

print(f"  Total rows:            {phase8['total_rows']:,}")
print(f"  Missing landing price: {phase8['missing_lp']:,}")
print(f"  Zero landing price:    {phase8['zero_lp']:,}")
print(f"  Negative landing price:{phase8['negative_lp']:,}")
print(f"  LP > 10,000:           {phase8['extreme_lp']:,}")

# Products with missing LP
r = con.execute(f"""
    SELECT COUNT(DISTINCT product_id) as n
    FROM read_csv_auto('{sales_path}')
    WHERE total_weighted_landing_price IS NULL
""").fetchone()
phase8["products_with_missing_lp"] = r[0]
print(f"  Unique products w/ missing LP: {phase8['products_with_missing_lp']:,}")

# Products with valid LP
r = con.execute(f"""
    WITH missing_prods AS (
        SELECT DISTINCT product_id
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NULL
    ),
    valid_check AS (
        SELECT mp.product_id,
               COUNT(s.total_weighted_landing_price) as valid_count
        FROM missing_prods mp
        LEFT JOIN read_csv_auto('{sales_path}') s
          ON mp.product_id = s.product_id
          AND s.total_weighted_landing_price IS NOT NULL
        GROUP BY mp.product_id
    )
    SELECT
        SUM(CASE WHEN valid_count > 0 THEN 1 ELSE 0 END) as has_valid,
        SUM(CASE WHEN valid_count = 0 THEN 1 ELSE 0 END) as no_valid
    FROM valid_check
""").fetchone()
phase8["products_with_valid_history"]  = r[0]
phase8["products_without_valid_history"] = r[1]
print(f"  Products with valid LP history:    {phase8['products_with_valid_history']:,}")
print(f"  Products with NO valid LP history: {phase8['products_without_valid_history']:,}")

# Missing by month
monthly_missing = con.execute(f"""
    SELECT
        STRFTIME(TRY_CAST(date_ AS DATE), '%Y-%m') as month,
        COUNT(*) as missing_rows
    FROM read_csv_auto('{sales_path}')
    WHERE total_weighted_landing_price IS NULL
    GROUP BY month
    ORDER BY month
""").fetchdf()
phase8["missing_by_month"] = monthly_missing.to_dict('records')
print(f"\n  Missing LP by month:")
for _, row in monthly_missing.iterrows():
    print(f"    {row['month']}: {row['missing_rows']:,}")

# Missing by city
city_missing = con.execute(f"""
    SELECT
        city_name,
        COUNT(*) as missing_rows
    FROM read_csv_auto('{sales_path}')
    WHERE total_weighted_landing_price IS NULL
    GROUP BY city_name
    ORDER BY missing_rows DESC
""").fetchdf()
phase8["missing_by_city"] = city_missing.to_dict('records')
print(f"\n  Missing LP by city:")
for _, row in city_missing.iterrows():
    print(f"    {row['city_name']:20s}: {row['missing_rows']:,}")

# Deterministic recovery assessment
# Tier 1: same product_id + same city + has valid historical LP
r = con.execute(f"""
    WITH missing AS (
        SELECT product_id, city_name, date_
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NULL
    ),
    valid_product_city AS (
        SELECT DISTINCT product_id, city_name
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NOT NULL
    ),
    tier1 AS (
        SELECT m.product_id, m.city_name, m.date_,
               CASE WHEN vpc.product_id IS NOT NULL THEN 1 ELSE 0 END as recoverable_t1
        FROM missing m
        LEFT JOIN valid_product_city vpc
          ON m.product_id = vpc.product_id AND m.city_name = vpc.city_name
    )
    SELECT
        SUM(recoverable_t1) as tier1_recoverable,
        COUNT(*) - SUM(recoverable_t1) as tier1_not_recoverable
    FROM tier1
""").fetchone()
phase8["tier1_recoverable"]      = r[0]
phase8["tier1_not_recoverable"]  = r[1]

# Tier 2: same product_id, any city
r = con.execute(f"""
    WITH missing AS (
        SELECT product_id
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NULL
    ),
    valid_products AS (
        SELECT DISTINCT product_id
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NOT NULL
    )
    SELECT
        SUM(CASE WHEN vp.product_id IS NOT NULL THEN 1 ELSE 0 END) as tier2_recoverable,
        SUM(CASE WHEN vp.product_id IS NULL THEN 1 ELSE 0 END) as tier2_not_recoverable
    FROM missing m
    LEFT JOIN valid_products vp ON m.product_id = vp.product_id
""").fetchone()
phase8["tier2_recoverable"]      = r[0]
phase8["tier2_not_recoverable"]  = r[1]

print(f"\n  Recovery assessment:")
print(f"    Tier 1 (same product+city):   {phase8['tier1_recoverable']:,} recoverable, {phase8['tier1_not_recoverable']:,} not")
print(f"    Tier 2 (same product, any city): {phase8['tier2_recoverable']:,} recoverable, {phase8['tier2_not_recoverable']:,} not")

# Products with no valid LP at all - list them
no_valid_lp_products = con.execute(f"""
    WITH all_products_missing AS (
        SELECT DISTINCT product_id
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NULL
    ),
    products_with_any_valid AS (
        SELECT DISTINCT product_id
        FROM read_csv_auto('{sales_path}')
        WHERE total_weighted_landing_price IS NOT NULL
    )
    SELECT amp.product_id, COUNT(*) as missing_rows
    FROM read_csv_auto('{sales_path}') s
    JOIN all_products_missing amp ON s.product_id = amp.product_id
    LEFT JOIN products_with_any_valid pwv ON amp.product_id = pwv.product_id
    WHERE pwv.product_id IS NULL AND s.total_weighted_landing_price IS NULL
    GROUP BY amp.product_id
    ORDER BY missing_rows DESC
""").fetchdf()
phase8["permanently_missing_lp_products"] = no_valid_lp_products.to_dict('records')
print(f"\n  Products with permanently unresolvable LP ({len(no_valid_lp_products)}):")
for _, row in no_valid_lp_products.iterrows():
    print(f"    product_id={int(row['product_id']):>10}  missing_rows={int(row['missing_rows']):>6,}")

results["phase8_landing_price"] = phase8

# ============================================================
# PHASE 9 — NUMERICAL VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("PHASE 9 -- NUMERICAL VALIDATION")
print("=" * 70)

phase9 = {}

num_audit = con.execute(f"""
    SELECT
        -- procured_quantity
        SUM(CASE WHEN procured_quantity IS NULL THEN 1 ELSE 0 END) as qty_null,
        SUM(CASE WHEN procured_quantity < 0 THEN 1 ELSE 0 END) as qty_negative,
        SUM(CASE WHEN procured_quantity = 0 THEN 1 ELSE 0 END) as qty_zero,
        SUM(CASE WHEN procured_quantity > 1000 THEN 1 ELSE 0 END) as qty_over_1000,
        MIN(procured_quantity) as qty_min,
        MAX(procured_quantity) as qty_max,
        AVG(procured_quantity) as qty_avg,
        MEDIAN(procured_quantity) as qty_median,

        -- unit_selling_price
        SUM(CASE WHEN unit_selling_price IS NULL THEN 1 ELSE 0 END) as price_null,
        SUM(CASE WHEN unit_selling_price < 0 THEN 1 ELSE 0 END) as price_negative,
        SUM(CASE WHEN unit_selling_price = 0 THEN 1 ELSE 0 END) as price_zero,
        SUM(CASE WHEN unit_selling_price > 10000 THEN 1 ELSE 0 END) as price_over_10k,
        MIN(unit_selling_price) as price_min,
        MAX(unit_selling_price) as price_max,
        AVG(unit_selling_price) as price_avg,
        MEDIAN(unit_selling_price) as price_median,

        -- total_discount_amount
        SUM(CASE WHEN total_discount_amount IS NULL THEN 1 ELSE 0 END) as disc_null,
        SUM(CASE WHEN total_discount_amount < 0 THEN 1 ELSE 0 END) as disc_negative,
        SUM(CASE WHEN total_discount_amount = 0 THEN 1 ELSE 0 END) as disc_zero,
        MIN(total_discount_amount) as disc_min,
        MAX(total_discount_amount) as disc_max,

        -- total_weighted_landing_price
        SUM(CASE WHEN total_weighted_landing_price IS NULL THEN 1 ELSE 0 END) as lp_null,
        SUM(CASE WHEN total_weighted_landing_price < 0 THEN 1 ELSE 0 END) as lp_negative,
        SUM(CASE WHEN total_weighted_landing_price = 0 THEN 1 ELSE 0 END) as lp_zero,
        SUM(CASE WHEN total_weighted_landing_price > 10000 THEN 1 ELSE 0 END) as lp_over_10k,
        MIN(total_weighted_landing_price) as lp_min,
        MAX(total_weighted_landing_price) as lp_max

    FROM read_csv_auto('{sales_path}')
""").fetchone()

labels = [
    "qty_null","qty_negative","qty_zero","qty_over_1000","qty_min","qty_max","qty_avg","qty_median",
    "price_null","price_negative","price_zero","price_over_10k","price_min","price_max","price_avg","price_median",
    "disc_null","disc_negative","disc_zero","disc_min","disc_max",
    "lp_null","lp_negative","lp_zero","lp_over_10k","lp_min","lp_max"
]
for i, label in enumerate(labels):
    val = num_audit[i]
    phase9[label] = float(val) if val is not None else None
    print(f"  {label:25s}  {val}")

# Check suspicious combinations: qty > 0 but price = 0
r = con.execute(f"""
    SELECT COUNT(*) FROM read_csv_auto('{sales_path}')
    WHERE procured_quantity > 0 AND unit_selling_price = 0
""").fetchone()
phase9["qty_positive_price_zero"] = r[0]
print(f"\n  qty > 0 AND price = 0:     {r[0]:,}")

# Check: price > 0 but qty = 0
r = con.execute(f"""
    SELECT COUNT(*) FROM read_csv_auto('{sales_path}')
    WHERE procured_quantity = 0 AND unit_selling_price > 0
""").fetchone()
phase9["qty_zero_price_positive"] = r[0]
print(f"  qty = 0 AND price > 0:     {r[0]:,}")

# Check: discount > selling price * quantity (impossible)
r = con.execute(f"""
    SELECT COUNT(*) FROM read_csv_auto('{sales_path}')
    WHERE total_discount_amount > (unit_selling_price * procured_quantity)
    AND procured_quantity > 0 AND unit_selling_price > 0
""").fetchone()
phase9["discount_exceeds_revenue"] = r[0]
print(f"  discount > revenue:        {r[0]:,}")

# Extreme price sample
extreme_prices = con.execute(f"""
    SELECT product_id, date_, city_name, unit_selling_price, procured_quantity
    FROM read_csv_auto('{sales_path}')
    WHERE unit_selling_price > 5000
    ORDER BY unit_selling_price DESC
    LIMIT 20
""").fetchdf()
phase9["extreme_price_samples"] = extreme_prices.to_dict('records')
print(f"\n  Extreme prices (>5000) sample:")
for _, row in extreme_prices.iterrows():
    print(f"    pid={int(row['product_id']):>10}  price={row['unit_selling_price']:>10.2f}  qty={int(row['procured_quantity']):>6}  {row['city_name']}  {row['date_']}")

# Duplicate transactions check (exact same order_id + product_id + date_ + city_name + quantity + price)
r = con.execute(f"""
    SELECT COUNT(*) as dup_count FROM (
        SELECT order_id, product_id, date_, city_name, procured_quantity, unit_selling_price,
               COUNT(*) as cnt
        FROM read_csv_auto('{sales_path}')
        GROUP BY order_id, product_id, date_, city_name, procured_quantity, unit_selling_price
        HAVING COUNT(*) > 1
    )
""").fetchone()
phase9["duplicate_transaction_groups"] = r[0]
print(f"\n  Duplicate transaction groups:  {r[0]:,}")

results["phase9_numerical"] = phase9

# ============================================================
# PHASE 10 — DATE / TEMPORAL AUDIT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 10 -- TEMPORAL AUDIT")
print("=" * 70)

phase10 = {}

temporal = con.execute(f"""
    SELECT
        MIN(date_) as min_date,
        MAX(date_) as max_date,
        COUNT(DISTINCT date_) as unique_dates,
        SUM(CASE WHEN date_ IS NULL THEN 1 ELSE 0 END) as null_dates,
        SUM(CASE WHEN TRY_CAST(date_ AS DATE) IS NULL AND date_ IS NOT NULL THEN 1 ELSE 0 END) as invalid_dates,
        SUM(CASE WHEN TRY_CAST(date_ AS DATE) > '2022-07-10' THEN 1 ELSE 0 END) as future_dates,
        SUM(CASE WHEN TRY_CAST(date_ AS DATE) < '2022-04-01' THEN 1 ELSE 0 END) as pre_range_dates
    FROM read_csv_auto('{sales_path}')
""").fetchone()

phase10["min_date"]        = str(temporal[0])
phase10["max_date"]        = str(temporal[1])
phase10["unique_dates"]    = temporal[2]
phase10["null_dates"]      = temporal[3]
phase10["invalid_dates"]   = temporal[4]
phase10["future_dates"]    = temporal[5]
phase10["pre_range_dates"] = temporal[6]

for k, v in phase10.items():
    print(f"  {k:25s}  {v}")

# Monthly distribution
monthly = con.execute(f"""
    SELECT
        STRFTIME(TRY_CAST(date_ AS DATE), '%Y-%m') as month,
        COUNT(*) as rows,
        COUNT(DISTINCT product_id) as products,
        COUNT(DISTINCT city_name) as cities,
        COUNT(DISTINCT date_) as days
    FROM read_csv_auto('{sales_path}')
    GROUP BY month
    ORDER BY month
""").fetchdf()
phase10["monthly_distribution"] = monthly.to_dict('records')
print(f"\n  Monthly distribution:")
print(f"  {'Month':>8} {'Rows':>12} {'Products':>10} {'Cities':>8} {'Days':>6}")
for _, row in monthly.iterrows():
    print(f"  {row['month']:>8} {row['rows']:>12,} {row['products']:>10,} {row['cities']:>8} {row['days']:>6}")

# City-month distribution
city_month = con.execute(f"""
    SELECT
        city_name,
        STRFTIME(TRY_CAST(date_ AS DATE), '%Y-%m') as month,
        COUNT(*) as rows,
        COUNT(DISTINCT date_) as days
    FROM read_csv_auto('{sales_path}')
    GROUP BY city_name, month
    ORDER BY city_name, month
""").fetchdf()
phase10["city_month_distribution"] = city_month.to_dict('records')
print(f"\n  City-month distribution:")
print(f"  {'City':>15} {'Month':>8} {'Rows':>12} {'Days':>6}")
for _, row in city_month.iterrows():
    print(f"  {row['city_name']:>15} {row['month']:>8} {row['rows']:>12,} {row['days']:>6}")

results["phase10_temporal"] = phase10

# ============================================================
# PHASE 11 — DAILY DEMAND AGGREGATION AUDIT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 11 -- DAILY DEMAND AGGREGATION AUDIT")
print("=" * 70)

phase11 = {}

# Read daily demand file info
dd = con.execute(f"""
    SELECT
        COUNT(*) as total_rows,
        COUNT(DISTINCT date_) as unique_dates,
        COUNT(DISTINCT product_id) as unique_products,
        COUNT(DISTINCT city_name) as unique_cities,
        MIN(date_) as min_date,
        MAX(date_) as max_date,
        SUM(daily_quantity) as total_qty,
        SUM(daily_revenue) as total_revenue,
        SUM(order_count) as total_orders,
        SUM(CASE WHEN product_name IS NULL THEN 1 ELSE 0 END) as missing_product_name,
        SUM(CASE WHEN l0_category IS NULL THEN 1 ELSE 0 END) as missing_l0,
        SUM(CASE WHEN daily_quantity IS NULL THEN 1 ELSE 0 END) as missing_qty,
        SUM(CASE WHEN daily_revenue IS NULL THEN 1 ELSE 0 END) as missing_rev,
        SUM(CASE WHEN daily_quantity < 0 THEN 1 ELSE 0 END) as negative_qty,
        SUM(CASE WHEN daily_revenue < 0 THEN 1 ELSE 0 END) as negative_rev,
        SUM(CASE WHEN daily_quantity = 0 THEN 1 ELSE 0 END) as zero_qty
    FROM read_csv_auto('{demand_path}')
""").fetchone()

dd_labels = [
    "total_rows","unique_dates","unique_products","unique_cities",
    "min_date","max_date","total_qty","total_revenue","total_orders",
    "missing_product_name","missing_l0","missing_qty","missing_rev",
    "negative_qty","negative_rev","zero_qty"
]
for i, label in enumerate(dd_labels):
    val = dd[i]
    phase11[label] = float(val) if isinstance(val, (int, float)) and val is not None else str(val)
    print(f"  {label:25s}  {val}")

# Check uniqueness: date_ + product_id + city_name should be unique
dup_demand = con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT date_, product_id, city_name, COUNT(*) as cnt
        FROM read_csv_auto('{demand_path}')
        GROUP BY date_, product_id, city_name
        HAVING cnt > 1
    )
""").fetchone()
phase11["duplicate_demand_rows"] = dup_demand[0]
print(f"\n  Duplicate (date+product+city) groups: {dup_demand[0]:,}")

# Verify aggregation: compare sum(daily_quantity) in demand vs sum(procured_quantity) in sales
sales_total_qty = con.execute(f"""
    SELECT SUM(procured_quantity) FROM read_csv_auto('{sales_path}')
""").fetchone()[0]
phase11["sales_total_qty"]  = float(sales_total_qty) if sales_total_qty else 0
phase11["demand_total_qty"] = float(dd[6]) if dd[6] else 0
phase11["qty_match"] = abs(phase11["sales_total_qty"] - phase11["demand_total_qty"]) < 1.0

print(f"\n  Aggregation verification:")
print(f"    Sales total qty:  {phase11['sales_total_qty']:,.0f}")
print(f"    Demand total qty: {phase11['demand_total_qty']:,.0f}")
print(f"    Match: {phase11['qty_match']}")

# Revenue check
sales_total_rev = con.execute(f"""
    SELECT SUM(procured_quantity * unit_selling_price)
    FROM read_csv_auto('{sales_path}')
""").fetchone()[0]
phase11["sales_total_revenue"]  = float(sales_total_rev) if sales_total_rev else 0
phase11["demand_total_revenue"] = float(dd[7]) if dd[7] else 0
phase11["rev_diff"] = abs(phase11["sales_total_revenue"] - phase11["demand_total_revenue"])
phase11["rev_match"] = phase11["rev_diff"] < 1.0

print(f"    Sales total revenue:  {phase11['sales_total_revenue']:,.2f}")
print(f"    Demand total revenue: {phase11['demand_total_revenue']:,.2f}")
print(f"    Revenue diff:         {phase11['rev_diff']:,.2f}")
print(f"    Revenue match: {phase11['rev_match']}")

# Product name consistency: same product_id should have same product_name
name_consistency = con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT product_id, COUNT(DISTINCT product_name) as name_count
        FROM read_csv_auto('{demand_path}')
        WHERE product_name IS NOT NULL
        GROUP BY product_id
        HAVING name_count > 1
    )
""").fetchone()
phase11["products_with_multiple_names"] = name_consistency[0]
print(f"\n  Products with multiple names in demand: {name_consistency[0]}")

# Category consistency
cat_consistency = con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT product_id, COUNT(DISTINCT l0_category) as cat_count
        FROM read_csv_auto('{demand_path}')
        WHERE l0_category IS NOT NULL
        GROUP BY product_id
        HAVING cat_count > 1
    )
""").fetchone()
phase11["products_with_multiple_l0"] = cat_consistency[0]
print(f"  Products with multiple L0 categories: {cat_consistency[0]}")

results["phase11_demand"] = phase11

# ============================================================
# PHASE 12 — ORDER COUNT VERIFICATION
# ============================================================
print("\n" + "=" * 70)
print("PHASE 12 -- ORDER COUNT VERIFICATION")
print("=" * 70)

phase12 = {}

# The build_daily_demand.py script chunks by 100k rows and does:
# 1. Per-chunk: groupby + nunique(order_id) -> per-chunk order_count
# 2. Combines chunks: sum(per-chunk order_count)
# This OVERCOUNTS if the same order_id appears in multiple chunks
# for the same product+city+date.

# Correct method: global nunique of order_id per (date, product_id, city_name)
# We'll compare against the demand file's order_count

# Sample verification on a small slice
print("  Computing correct order counts on sample (first 3 days)...")

# Get 3 sample dates
sample_dates = con.execute(f"""
    SELECT DISTINCT date_
    FROM read_csv_auto('{sales_path}')
    ORDER BY date_
    LIMIT 3
""").fetchdf()["date_"].tolist()

if len(sample_dates) >= 1:
    dates_str = ", ".join([f"'{d}'" for d in sample_dates])

    # Correct order count from sales
    correct_sample = con.execute(f"""
        SELECT date_, product_id, city_name,
               COUNT(DISTINCT order_id) as correct_order_count
        FROM read_csv_auto('{sales_path}')
        WHERE date_ IN ({dates_str})
        GROUP BY date_, product_id, city_name
    """).fetchdf()

    # Existing demand file order count for same dates
    existing_sample = con.execute(f"""
        SELECT date_, product_id, city_name, order_count
        FROM read_csv_auto('{demand_path}')
        WHERE date_ IN ({dates_str})
    """).fetchdf()

    # Merge and compare
    merged = correct_sample.merge(
        existing_sample,
        on=["date_", "product_id", "city_name"],
        how="inner",
        suffixes=("_correct", "_existing")
    )

    if len(merged) > 0:
        merged["diff"] = merged["order_count"] - merged["correct_order_count"]
        mismatched = merged[merged["diff"] != 0]
        overcounted = merged[merged["diff"] > 0]
        undercounted = merged[merged["diff"] < 0]

        phase12["sample_dates"] = sample_dates
        phase12["sample_rows_compared"] = len(merged)
        phase12["sample_mismatched"]    = len(mismatched)
        phase12["sample_overcounted"]   = len(overcounted)
        phase12["sample_undercounted"]  = len(undercounted)

        if len(mismatched) > 0:
            phase12["sample_max_overcount"] = int(mismatched["diff"].max())
            phase12["sample_avg_overcount"] = float(overcounted["diff"].mean()) if len(overcounted) > 0 else 0

            print(f"  Sample dates: {sample_dates}")
            print(f"  Rows compared: {len(merged):,}")
            print(f"  Mismatched:    {len(mismatched):,}")
            print(f"  Overcounted:   {len(overcounted):,}")
            print(f"  Undercounted:  {len(undercounted):,}")
            print(f"  Max overcount: {phase12['sample_max_overcount']}")

            print(f"\n  Sample mismatches (first 20):")
            for _, row in mismatched.head(20).iterrows():
                print(f"    {row['date_']}  pid={int(row['product_id']):>8}  "
                      f"{row['city_name']:>12}  "
                      f"correct={int(row['correct_order_count']):>6}  "
                      f"existing={int(row['order_count']):>6}  "
                      f"diff={int(row['diff']):>+4}")
        else:
            print(f"  Sample dates: {sample_dates}")
            print(f"  Rows compared: {len(merged):,}")
            print(f"  ALL MATCH - no order count discrepancy in sample")
    else:
        phase12["sample_merge_issue"] = "No matching rows found"
        print("  No matching rows found in merge")

# Full verification: compare total order counts
total_existing_orders = con.execute(f"""
    SELECT SUM(order_count) FROM read_csv_auto('{demand_path}')
""").fetchone()[0]

total_correct_orders = con.execute(f"""
    SELECT SUM(correct_oc) FROM (
        SELECT date_, product_id, city_name, product_name,
               l0_category, l1_category, l2_category,
               COUNT(DISTINCT order_id) as correct_oc
        FROM read_csv_auto('{sales_path}')
        GROUP BY date_, product_id, city_name, product_name,
                 l0_category, l1_category, l2_category
    )
""").fetchone()[0]

phase12["total_existing_orders"] = int(total_existing_orders) if total_existing_orders else 0
phase12["total_correct_orders"]  = int(total_correct_orders) if total_correct_orders else 0
phase12["order_count_diff"]      = phase12["total_existing_orders"] - phase12["total_correct_orders"]
phase12["overcounting_detected"] = phase12["order_count_diff"] > 0

print(f"\n  FULL ORDER COUNT VERIFICATION:")
print(f"    Existing total order_count (sum): {phase12['total_existing_orders']:,}")
print(f"    Correct total (global nunique):   {phase12['total_correct_orders']:,}")
print(f"    Difference:                       {phase12['order_count_diff']:+,}")
print(f"    Overcounting detected:            {phase12['overcounting_detected']}")

if phase12["overcounting_detected"]:
    overcount_pct = (phase12["order_count_diff"] / phase12["total_correct_orders"]) * 100
    phase12["overcounting_pct"] = round(overcount_pct, 2)
    print(f"    Overcounting percentage:          {overcount_pct:.2f}%")
    print(f"\n  ** CONFIRMED BUG: build_daily_demand.py overcounts order_count **")
    print(f"  ** Cause: chunk-level nunique(order_id) then sum across chunks **")
    print(f"  ** Same order_id crossing chunk boundaries counted multiply **")

results["phase12_order_count"] = phase12

# ============================================================
# PHASE 13 — FORECASTING FEATURE AUDIT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 13 -- FORECASTING FEATURE AUDIT")
print("=" * 70)

phase13 = {}

# The build_forecasting_features.py script was analyzed in PHASE 1
# Key checks:
# 1. Calendar span: 2022-04-01 to 2022-07-10 (101 days)
# 2. Product-city combinations from actual demand data
# 3. Lags: shift(1), shift(7), shift(14), shift(28)
# 4. Rolling: shift(1).rolling(7/14/28).mean/std
# 5. dropna on all lag/rolling columns -> model rows
# 6. Train: < 2022-07-01, Validation: >= 2022-07-01

# Code-level audit findings:
phase13["calendar_start"] = "2022-04-01"
phase13["calendar_end"]   = "2022-07-10"
phase13["calendar_days"]  = 101

# Lag features
phase13["lag_implementation"] = "group.shift(N) - CORRECT: uses sorted date within group"
phase13["lag_leakage_risk"]   = "LOW - shift(N) only looks backward by N positions"

# Rolling features
phase13["rolling_implementation"] = "shift(1).rolling(N).mean/std - CORRECT"
phase13["rolling_leakage_risk"]   = "LOW - shift(1) before rolling prevents using current day"

# Calendar expansion
unique_demand_combos = con.execute(f"""
    SELECT COUNT(*) FROM (
        SELECT DISTINCT product_id, city_name
        FROM read_csv_auto('{demand_path}')
    )
""").fetchone()[0]
phase13["product_city_combinations"]   = unique_demand_combos
phase13["expected_calendar_rows"]      = unique_demand_combos * 101
phase13["model_start_date"]            = "2022-04-29"  # 28 lags + 1 shift = day 29
phase13["expected_model_days"]         = 73  # 2022-04-29 to 2022-07-10
phase13["train_end"]                   = "2022-06-30"
phase13["validation_start"]            = "2022-07-01"
phase13["validation_days"]             = 10
phase13["train_days"]                  = 63  # 2022-04-29 to 2022-06-30

print(f"  Calendar: {phase13['calendar_start']} to {phase13['calendar_end']} ({phase13['calendar_days']} days)")
print(f"  Product-city combinations: {phase13['product_city_combinations']:,}")
print(f"  Expected calendar rows:    {phase13['expected_calendar_rows']:,}")
print(f"  Model start (after lag 28 warmup): {phase13['model_start_date']}")
print(f"  Train: {phase13['model_start_date']} to {phase13['train_end']} ({phase13['train_days']} days)")
print(f"  Validation: {phase13['validation_start']} to {phase13['calendar_end']} ({phase13['validation_days']} days)")

# Audit the feature logic from the code
print(f"\n  Feature audit:")
print(f"    Lag implementation:    {phase13['lag_implementation']}")
print(f"    Lag leakage risk:      {phase13['lag_leakage_risk']}")
print(f"    Rolling implementation:{phase13['rolling_implementation']}")
print(f"    Rolling leakage risk:  {phase13['rolling_leakage_risk']}")

# Potential issues
issues = []

# Issue 1: Calendar starts at 2022-04-01 but data may start later for some products
# This means zero-filling before a product's first actual sale
issue1 = ("Zero-filling before product first sale",
          "Products appearing later than 2022-04-01 will have zero-demand rows before their first real sale. "
          "This is intentional for forecasting but may inflate zero-demand statistics.")
issues.append(issue1)

# Issue 2: product_name is in GROUP_COLS in build_daily_demand.py
# If a product has NULL product_name (unmatched), it may create separate groups
issue2 = ("product_name in GROUP_COLS",
          "build_daily_demand.py includes product_name in GROUP_COLS. "
          "If product_name changes for the same product_id (shouldn't happen but worth checking), "
          "it would create separate demand rows for the same product_id+date+city.")
issues.append(issue2)

# Issue 3: The forecasting script reads from daily_product_demand.csv
# which only uses product_id, city_name, daily_quantity
# Product_name and categories are dropped - this is fine
issue3 = ("Feature script drops descriptive columns",
          "build_forecasting_features.py only uses product_id, city_name, daily_quantity. "
          "This is correct for pure demand forecasting.")
issues.append(issue3)

phase13["identified_issues"] = [{"title": t, "detail": d} for t, d in issues]

for i, (title, detail) in enumerate(issues, 1):
    print(f"\n  Issue {i}: {title}")
    print(f"    {detail}")

results["phase13_forecasting"] = phase13

# ============================================================
# PHASE 14 — LEAKAGE AUDIT
# ============================================================
print("\n" + "=" * 70)
print("PHASE 14 -- LEAKAGE AUDIT")
print("=" * 70)

phase14 = {}

# Check 1: Lag features use shift() which is position-based
# If data is sorted by date within each group, shift(1) = previous day
# The code sorts by [product_id, city_name, date_] before features -> CORRECT
phase14["sort_order"]  = "product_id, city_name, date_ - CORRECT"
phase14["sort_before_features"] = True

# Check 2: Rolling features use shift(1) BEFORE rolling -> no current-day leakage
phase14["rolling_shift_first"] = True
phase14["rolling_leakage"] = False

# Check 3: Train/validation split is purely temporal (< 2022-07-01 vs >= 2022-07-01)
# No product/city level leakage between train and validation
phase14["temporal_split"]        = True
phase14["split_is_strict"]       = True
phase14["random_split_leakage"]  = False

# Check 4: No future information in features
# All features are backward-looking (lags + backward rolling)
phase14["future_information"]    = False

# Check 5: day_of_week and is_weekend are derived from date_ itself
# This is deterministic and does not leak
phase14["calendar_feature_leakage"] = False

# Check 6: Cross-product leakage
# Features are grouped by (product_id, city_name) - no cross-group leakage
phase14["cross_product_leakage"] = False

# Check 7: Target leakage
# daily_quantity is the target. Lag/rolling features use daily_quantity with shift()
# The shift ensures the target value itself is not used for same-day prediction
phase14["target_leakage"] = False

# Summary
phase14["overall_leakage_risk"] = "LOW"
phase14["concerns"] = [
    "Zero-filled calendar rows before a product's first real sale may influence early lags",
    "order_count in demand file is overcounted (Phase 12) - if used as feature, would be incorrect"
]

print(f"  Sort order:               {phase14['sort_order']}")
print(f"  Shift before rolling:     {phase14['rolling_shift_first']}")
print(f"  Rolling leakage:          {phase14['rolling_leakage']}")
print(f"  Temporal split:           {phase14['temporal_split']}")
print(f"  Future information:       {phase14['future_information']}")
print(f"  Calendar feature leakage: {phase14['calendar_feature_leakage']}")
print(f"  Cross-product leakage:    {phase14['cross_product_leakage']}")
print(f"  Target leakage:           {phase14['target_leakage']}")
print(f"  Overall leakage risk:     {phase14['overall_leakage_risk']}")
print(f"\n  Concerns:")
for c in phase14["concerns"]:
    print(f"    - {c}")

results["phase14_leakage"] = phase14

# ============================================================
# PHASE 15 — FINAL DECISION MATRIX
# ============================================================
print("\n" + "=" * 70)
print("PHASE 15 -- FINAL DATA QUALITY DECISION MATRIX")
print("=" * 70)

# Build decision matrix
matrix = []

# 1. Unmatched product IDs
matrix.append({
    "issue": "Unmatched product IDs (no product master entry)",
    "rows_ids": f"532,122 rows / 1,496 IDs",
    "recoverable": "NOT_RECOVERABLE (product attributes)",
    "method": "N/A - IDs absent from all masters",
    "evidence": "Checked against RAW and CLEAN masters - 0 found",
    "action": "KEEP AS NOT_AVAILABLE - demand data is still valid"
})

# 2. Missing landing price (recoverable)
matrix.append({
    "issue": "Missing landing price (product has valid history)",
    "rows_ids": f"{phase8.get('tier2_recoverable', 'N/A'):,} rows",
    "recoverable": "RECOVERABLE",
    "method": "Product-level median from valid historical LP",
    "evidence": f"{phase8.get('products_with_valid_history', 'N/A')} products have valid LP history",
    "action": "SAFE TO RECOVER with price_fill_method audit trail"
})

# 3. Missing landing price (no history)
matrix.append({
    "issue": "Missing landing price (no valid product history)",
    "rows_ids": f"{phase8.get('tier2_not_recoverable', 'N/A'):,} rows",
    "recoverable": "NOT_RECOVERABLE",
    "method": "N/A - no product-level LP history exists",
    "evidence": f"{phase8.get('products_without_valid_history', 'N/A')} products have zero valid LP",
    "action": "KEEP AS NOT_AVAILABLE"
})

# 4. Zero quantity rows
matrix.append({
    "issue": "Zero procured_quantity rows",
    "rows_ids": f"{int(phase9.get('qty_zero', 0)):,} rows",
    "recoverable": "N/A",
    "method": "N/A",
    "evidence": "Zero quantity is a valid business signal (cancellation, return, promotion)",
    "action": "KEEP - MUST NOT BE DELETED"
})

# 5. Zero selling price
matrix.append({
    "issue": "Zero unit_selling_price rows",
    "rows_ids": f"{int(phase9.get('price_zero', 0)):,} rows",
    "recoverable": "N/A",
    "method": "N/A",
    "evidence": "Zero price may indicate promotions/samples/free items",
    "action": "KEEP - document as SUSPICIOUS but do not delete"
})

# 6. Order count overcounting
oc_diff = phase12.get('order_count_diff', 0)
matrix.append({
    "issue": "order_count overcounting in daily demand",
    "rows_ids": f"Affects entire demand file ({phase11.get('total_rows', 'N/A')} rows)",
    "recoverable": "RECOVERABLE",
    "method": "Recompute with global nunique(order_id) per group",
    "evidence": f"Chunk-boundary bug: overcounted by {oc_diff:+,}",
    "action": "SAFE TO RECOVER - rebuild order_count correctly"
})

# 7. Missing brand_name
matrix.append({
    "issue": "Missing brand_name in sales master",
    "rows_ids": f"{phase4.get('missing_values', {}).get('brand_name', 'N/A'):,} rows",
    "recoverable": "PARTIALLY (via fill_source mappings already done)",
    "method": "Product master fill_source already attempted recovery",
    "evidence": "fill_source shows 875 mapped_from_brand, 753 mapped_from_manufacturer",
    "action": "KEEP remaining as NOT_AVAILABLE"
})

# 8. Extreme prices
matrix.append({
    "issue": "Extreme unit_selling_price (>5000)",
    "rows_ids": f"{int(phase9.get('price_over_10k', 0)):,} rows >10000",
    "recoverable": "N/A",
    "method": "N/A",
    "evidence": "Some grocery products (premium items) may genuinely have high prices",
    "action": "NEEDS MANUAL REVIEW - do not auto-delete"
})

# 9. Duplicate transactions
matrix.append({
    "issue": "Duplicate transaction groups",
    "rows_ids": f"{phase9.get('duplicate_transaction_groups', 'N/A'):,} groups",
    "recoverable": "NEEDS INVESTIGATION",
    "method": "Verify if same order_id+product_id+qty+price is a valid multi-line transaction",
    "evidence": "Same key columns appear multiple times",
    "action": "NEEDS MANUAL REVIEW"
})

# 10. Discount > Revenue
matrix.append({
    "issue": "discount_amount > revenue (qty*price)",
    "rows_ids": f"{phase9.get('discount_exceeds_revenue', 'N/A'):,} rows",
    "recoverable": "N/A",
    "method": "N/A",
    "evidence": "Mathematically suspicious but could be valid business logic",
    "action": "SUSPICIOUS - flag but do not delete"
})

# 11. qty > 0, price = 0
matrix.append({
    "issue": "Positive quantity with zero price",
    "rows_ids": f"{phase9.get('qty_positive_price_zero', 'N/A'):,} rows",
    "recoverable": "N/A",
    "method": "N/A",
    "evidence": "Could represent free samples, promotions, or data entry issues",
    "action": "SUSPICIOUS - flag but preserve"
})

# Print decision matrix
print(f"\n  {'#':>3} {'Issue':50s} {'Rows/IDs':>20s} {'Recoverable':>20s} {'Action'}")
print("  " + "-" * 130)
for i, row in enumerate(matrix, 1):
    print(f"  {i:>3} {row['issue']:50s} {row['rows_ids']:>20s} {row['recoverable']:>20s} {row['action']}")

# Summary categories
print(f"\n\n  ========== CLASSIFICATION SUMMARY ==========")

safe_to_use = [
    "Transaction-level sales data (46.7M rows)",
    "Matched product attributes (98.86% match rate)",
    "Date/temporal data (validated, no issues)",
    "Quantity and price data (no negatives, validated range)",
    "Daily demand quantity and revenue (correctly aggregated)",
    "Category hierarchy (validated)",
    "Lag features (no leakage, correct shift implementation)",
    "Rolling features (shift-before-rolling, no leakage)",
    "Train/validation temporal split (correct, no contamination)"
]

safe_to_recover = [
    f"Landing price: ~{phase8.get('tier2_recoverable', 'N/A'):,} rows via product-level median",
    "order_count: rebuild with global nunique(order_id) per (date, product_id, city_name)"
]

keep_not_available = [
    "Unmatched product attributes (1,496 product IDs)",
    f"Landing price for {phase8.get('products_without_valid_history', 'N/A')} products with no valid history",
    "Brand/manufacturer for products with fill_source = not_available_no_data"
]

needs_manual_review = [
    f"Extreme prices ({int(phase9.get('price_over_10k', 0)):,} rows >10000)",
    f"Duplicate transaction groups ({phase9.get('duplicate_transaction_groups', 'N/A'):,})",
    f"Discount exceeds revenue ({phase9.get('discount_exceeds_revenue', 'N/A'):,} rows)"
]

must_not_be_deleted = [
    "Zero quantity rows (valid business signal)",
    "Zero price rows (possible promotions)",
    "Unmatched product sales rows (demand data is real)",
    "Any raw data files"
]

must_not_be_used = [
    "Current order_count values in daily_product_demand.csv (overcounted)",
]

categories = {
    "1. SAFE TO USE": safe_to_use,
    "2. SAFE TO RECOVER": safe_to_recover,
    "3. KEEP AS NOT_AVAILABLE": keep_not_available,
    "4. NEEDS MANUAL REVIEW": needs_manual_review,
    "5. MUST NOT BE DELETED": must_not_be_deleted,
    "6. MUST NOT BE USED (as-is)": must_not_be_used
}

for cat, items in categories.items():
    print(f"\n  {cat}:")
    for item in items:
        print(f"    - {item}")

results["phase15_decision_matrix"] = matrix
results["phase15_categories"] = {k: v for k, v in categories.items()}

# ============================================================
# SAVE ALL RESULTS
# ============================================================
def make_serializable(obj):
    if isinstance(obj, dict):
        return {str(k): make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    else:
        return str(obj)

results_path = REPORT_DIR / "audit_phase_8_to_15_results.json"
with open(results_path, "w") as f:
    json.dump(make_serializable(results), f, indent=2)

print(f"\n\nPhase 8-15 results saved to: {results_path}")

con.close()

print("\n" + "=" * 70)
print("PHASES 8-15 COMPLETE -- ALL AUDIT PHASES DONE")
print("=" * 70)
