"""
DEMAND DECISION INTELLIGENCE — DATA FORENSIC AUDIT
Phases 1–7: Project Inventory, Product Masters, Sales Validation,
            Unmatched Product Forensics, Attribute Recoverability
"""
import pandas as pd
import duckdb
import json
import os
from pathlib import Path
from collections import Counter

PROJECT = Path(__file__).resolve().parent.parent

# Output directory
REPORT_DIR = PROJECT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# File paths
RAW_PRODUCT   = PROJECT / "dataset" / "raw" / "products" / "dim_product.csv"
CLEAN_PRODUCT = PROJECT / "dataset" / "cleaned" / "dim_product_cleaned_with_audit.csv"
SALES_MASTER  = PROJECT / "dataset" / "cleaned" / "sales_product_master.csv"
DAILY_DEMAND  = PROJECT / "dataset" / "processed" / "daily_product_demand.csv"

RAW_SALES_DIR = PROJECT / "dataset" / "raw" / "sales"

results = {}   # accumulate all findings

# ============================================================
# PHASE 1 — PROJECT INVENTORY
# ============================================================
print("=" * 70)
print("PHASE 1 — PROJECT FILE INVENTORY")
print("=" * 70)

inventory = {}

def file_info(p):
    if p.exists():
        size_mb = p.stat().st_size / (1024**2)
        return {"exists": True, "size_mb": round(size_mb, 2)}
    return {"exists": False, "size_mb": 0}

inventory["raw_product_master"]     = file_info(RAW_PRODUCT)
inventory["cleaned_product_master"] = file_info(CLEAN_PRODUCT)
inventory["cleaned_product_no_audit"] = file_info(
    PROJECT / "dataset" / "cleaned" / "dim_product_cleaned.csv"
)
inventory["sales_product_master"]   = file_info(SALES_MASTER)
inventory["daily_product_demand"]   = file_info(DAILY_DEMAND)

raw_sales_files = sorted(RAW_SALES_DIR.glob("fact_sales_*.csv"))
for f in raw_sales_files:
    inventory[f"raw_sales/{f.name}"] = file_info(f)

for k, v in inventory.items():
    status = "[OK]" if v["exists"] else "[MISSING]"
    print(f"  {status:12s}  {v['size_mb']:>10.2f} MB   {k}")

results["phase1_inventory"] = inventory

# ============================================================
# PHASE 2 — RAW PRODUCT MASTER VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("PHASE 2 — RAW PRODUCT MASTER VALIDATION")
print("=" * 70)

raw_prod = pd.read_csv(RAW_PRODUCT, low_memory=False)
phase2 = {}

phase2["total_rows"]       = len(raw_prod)
phase2["columns"]          = list(raw_prod.columns)
phase2["unique_product_ids"] = raw_prod["product_id"].nunique()
phase2["duplicate_product_ids"] = int(raw_prod["product_id"].duplicated().sum())

# Missing values
missing_raw = raw_prod.isnull().sum()
phase2["missing_values"] = {c: int(v) for c, v in missing_raw.items() if v > 0}

# ID range
phase2["min_product_id"] = int(raw_prod["product_id"].min())
phase2["max_product_id"] = int(raw_prod["product_id"].max())

# Check for 'Unnamed: 0' column
phase2["has_unnamed_index_col"] = "Unnamed: 0" in raw_prod.columns

print(f"  Rows:              {phase2['total_rows']:,}")
print(f"  Columns:           {len(phase2['columns'])}")
print(f"  Unique product_id: {phase2['unique_product_ids']:,}")
print(f"  Duplicate IDs:     {phase2['duplicate_product_ids']:,}")
print(f"  ID range:          {phase2['min_product_id']} – {phase2['max_product_id']}")
print(f"  Missing values:")
for col, cnt in phase2["missing_values"].items():
    print(f"    {col:30s}  {cnt:,}")

results["phase2_raw_product"] = phase2

# ============================================================
# PHASE 3 — CLEANED PRODUCT MASTER VALIDATION
# ============================================================
print("\n" + "=" * 70)
print("PHASE 3 — CLEANED PRODUCT MASTER VALIDATION")
print("=" * 70)

clean_prod = pd.read_csv(CLEAN_PRODUCT, low_memory=False)
phase3 = {}

phase3["total_rows"]       = len(clean_prod)
phase3["columns"]          = list(clean_prod.columns)
phase3["unique_product_ids"] = clean_prod["product_id"].nunique()
phase3["duplicate_product_ids"] = int(clean_prod["product_id"].duplicated().sum())
phase3["has_fill_source"]  = "fill_source" in clean_prod.columns

# Missing values
missing_clean = clean_prod.isnull().sum()
phase3["missing_values"] = {c: int(v) for c, v in missing_clean.items() if v > 0}

# fill_source distribution
if phase3["has_fill_source"]:
    fs_dist = clean_prod["fill_source"].value_counts().to_dict()
    phase3["fill_source_distribution"] = {str(k): int(v) for k, v in fs_dist.items()}
else:
    phase3["fill_source_distribution"] = "COLUMN MISSING"

# ID range
phase3["min_product_id"] = int(clean_prod["product_id"].min())
phase3["max_product_id"] = int(clean_prod["product_id"].max())

print(f"  Rows:              {phase3['total_rows']:,}")
print(f"  Unique product_id: {phase3['unique_product_ids']:,}")
print(f"  Duplicate IDs:     {phase3['duplicate_product_ids']:,}")
print(f"  ID range:          {phase3['min_product_id']} – {phase3['max_product_id']}")
print(f"  Missing values:    {phase3['missing_values'] if phase3['missing_values'] else 'NONE'}")
print(f"  fill_source column present: {phase3['has_fill_source']}")
if isinstance(phase3["fill_source_distribution"], dict):
    print(f"  fill_source distribution:")
    for k, v in phase3["fill_source_distribution"].items():
        print(f"    {k:30s}  {v:,}")

# Cross-validate RAW vs CLEAN
raw_ids  = set(raw_prod["product_id"].dropna().astype(int))
clean_ids = set(clean_prod["product_id"].dropna().astype(int))

phase3["raw_ids_missing_from_clean"] = len(raw_ids - clean_ids)
phase3["clean_ids_not_in_raw"]       = len(clean_ids - raw_ids)
phase3["ids_in_both"]                = len(raw_ids & clean_ids)

print(f"\n  Cross-validation RAW vs CLEAN:")
print(f"    RAW IDs missing from CLEAN:  {phase3['raw_ids_missing_from_clean']}")
print(f"    CLEAN IDs not in RAW:        {phase3['clean_ids_not_in_raw']}")
print(f"    IDs in both:                 {phase3['ids_in_both']:,}")

# Check field-level consistency between RAW and CLEAN for shared IDs
# Compare a sample of 500 shared IDs
sample_size = min(500, len(raw_ids & clean_ids))
import random
random.seed(42)
sample_ids = random.sample(sorted(raw_ids & clean_ids), sample_size)

raw_sample = raw_prod[raw_prod["product_id"].isin(sample_ids)].set_index("product_id")
clean_sample = clean_prod[clean_prod["product_id"].isin(sample_ids)].set_index("product_id")

compare_cols = ["product_name", "l0_category", "l1_category", "l2_category"]
consistency_issues = {}
for col in compare_cols:
    if col in raw_sample.columns and col in clean_sample.columns:
        merged = raw_sample[[col]].join(clean_sample[[col]], lsuffix="_raw", rsuffix="_clean")
        # Only compare where both are non-null
        both_filled = merged.dropna()
        mismatches = (both_filled.iloc[:, 0] != both_filled.iloc[:, 1]).sum()
        consistency_issues[col] = {
            "compared": len(both_filled),
            "mismatches": int(mismatches)
        }

phase3["raw_vs_clean_consistency"] = consistency_issues
print(f"\n  Field consistency (sample of {sample_size} shared IDs):")
for col, info in consistency_issues.items():
    print(f"    {col:20s}  compared: {info['compared']}  mismatches: {info['mismatches']}")

results["phase3_clean_product"] = phase3

# ============================================================
# PHASE 4 — SALES PRODUCT MASTER VALIDATION (via DuckDB)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 4 — SALES PRODUCT MASTER VALIDATION")
print("=" * 70)

con = duckdb.connect()
sales_path = str(SALES_MASTER).replace("\\", "/")

phase4 = {}

# Total rows
r = con.execute(f"SELECT COUNT(*) as cnt FROM read_csv_auto('{sales_path}')").fetchone()
phase4["total_rows"] = r[0]
print(f"  Total rows: {phase4['total_rows']:,}")

# Column names
cols_r = con.execute(f"SELECT * FROM read_csv_auto('{sales_path}') LIMIT 0").description
phase4["columns"] = [c[0] for c in cols_r]
print(f"  Columns: {phase4['columns']}")

# Unique product IDs
r = con.execute(f"SELECT COUNT(DISTINCT product_id) FROM read_csv_auto('{sales_path}')").fetchone()
phase4["unique_product_ids"] = r[0]
print(f"  Unique product_id: {phase4['unique_product_ids']:,}")

# Missing values for key columns
key_cols = [
    "date_", "city_name", "order_id", "product_id",
    "procured_quantity", "unit_selling_price",
    "total_discount_amount", "total_weighted_landing_price",
    "product_name", "brand_name", "manufacturer_name",
    "l0_category", "l1_category", "l2_category"
]
missing_sales = {}
for col in key_cols:
    r = con.execute(f"""
        SELECT COUNT(*) - COUNT("{col}") as missing
        FROM read_csv_auto('{sales_path}')
    """).fetchone()
    if r[0] > 0:
        missing_sales[col] = r[0]

phase4["missing_values"] = missing_sales
print(f"  Missing values in sales master:")
for col, cnt in missing_sales.items():
    print(f"    {col:40s}  {cnt:,}")

# Date range
r = con.execute(f"""
    SELECT MIN(date_), MAX(date_), COUNT(DISTINCT date_)
    FROM read_csv_auto('{sales_path}')
""").fetchone()
phase4["date_min"] = str(r[0])
phase4["date_max"] = str(r[1])
phase4["unique_dates"] = r[2]
print(f"  Date range: {phase4['date_min']} to {phase4['date_max']} ({phase4['unique_dates']} unique)")

# Unique cities
r = con.execute(f"SELECT DISTINCT city_name FROM read_csv_auto('{sales_path}') ORDER BY city_name").fetchall()
phase4["cities"] = [x[0] for x in r]
print(f"  Cities: {phase4['cities']}")

results["phase4_sales"] = phase4

# ============================================================
# PHASE 5 — UNMATCHED PRODUCT ID FORENSICS (via DuckDB)
# ============================================================
print("\n" + "=" * 70)
print("PHASE 5 — UNMATCHED PRODUCT ID FORENSICS")
print("=" * 70)

phase5 = {}

# Find unmatched product IDs (where product_name is NULL = unmatched)
r = con.execute(f"""
    SELECT COUNT(*) as unmatched_rows,
           COUNT(DISTINCT product_id) as unmatched_ids
    FROM read_csv_auto('{sales_path}')
    WHERE product_name IS NULL
""").fetchone()
phase5["unmatched_rows"] = r[0]
phase5["unmatched_unique_ids"] = r[1]
print(f"  Unmatched rows (product_name IS NULL): {phase5['unmatched_rows']:,}")
print(f"  Unique unmatched product IDs:          {phase5['unmatched_unique_ids']:,}")

# Detailed per-product forensics for all unmatched IDs
print("  Computing per-product forensics for unmatched IDs...")
unmatched_detail = con.execute(f"""
    SELECT
        product_id,
        COUNT(*) as total_rows,
        SUM(procured_quantity) as total_qty,
        SUM(procured_quantity * unit_selling_price) as total_revenue,
        MIN(date_) as first_date,
        MAX(date_) as last_date,
        COUNT(DISTINCT date_) as active_days,
        COUNT(DISTINCT city_name) as num_cities,
        STRING_AGG(DISTINCT city_name, ', ' ORDER BY city_name) as cities,
        COUNT(DISTINCT STRFTIME(TRY_CAST(date_ AS DATE), '%Y-%m')) as num_months,
        STRING_AGG(DISTINCT STRFTIME(TRY_CAST(date_ AS DATE), '%Y-%m'), ', ') as months,
        MIN(unit_selling_price) as min_price,
        MAX(unit_selling_price) as max_price,
        AVG(unit_selling_price) as avg_price,
        MEDIAN(unit_selling_price) as median_price,
        MIN(procured_quantity) as min_qty,
        MAX(procured_quantity) as max_qty,
        AVG(procured_quantity) as avg_qty,
        STDDEV(unit_selling_price) as std_price
    FROM read_csv_auto('{sales_path}')
    WHERE product_name IS NULL
    GROUP BY product_id
    ORDER BY total_rows DESC
""").fetchdf()

phase5["detail_shape"] = unmatched_detail.shape

# Classify unmatched products
def classify_unmatched(row):
    """Evidence-based classification."""
    if row["total_rows"] >= 50 and row["num_cities"] >= 2 and row["num_months"] >= 2:
        return "A_recurring_strong_evidence"
    elif row["total_rows"] >= 10 and (row["num_cities"] >= 2 or row["num_months"] >= 2):
        return "A_recurring_moderate_evidence"
    elif row["total_rows"] >= 5:
        return "B_low_frequency"
    elif row["total_rows"] >= 2:
        if row["min_price"] == 0 and row["max_price"] == 0:
            return "C_suspicious_anomalous"
        return "B_low_frequency"
    else:
        if row["total_qty"] == 0 or (row["min_price"] == 0 and row["max_price"] == 0):
            return "C_suspicious_anomalous"
        return "D_unresolved_single_occurrence"

unmatched_detail["classification"] = unmatched_detail.apply(classify_unmatched, axis=1)

classification_summary = unmatched_detail["classification"].value_counts().to_dict()
phase5["classification_summary"] = {str(k): int(v) for k, v in classification_summary.items()}

print(f"\n  Classification summary:")
for cat, cnt in sorted(phase5["classification_summary"].items()):
    print(f"    {cat:45s}  {cnt:,}")

# Summary stats
phase5["total_unmatched_qty"]     = float(unmatched_detail["total_qty"].sum())
phase5["total_unmatched_revenue"] = float(unmatched_detail["total_revenue"].sum())

multi_city  = int((unmatched_detail["num_cities"] > 1).sum())
multi_month = int((unmatched_detail["num_months"] > 1).sum())
phase5["multi_city_ids"]  = multi_city
phase5["multi_month_ids"] = multi_month

print(f"\n  Total unmatched quantity:  {phase5['total_unmatched_qty']:,.0f}")
print(f"  Total unmatched revenue:  ₹{phase5['total_unmatched_revenue']:,.0f}")
print(f"  IDs in multiple cities:   {multi_city}")
print(f"  IDs in multiple months:   {multi_month}")

# Top 30 unmatched
print(f"\n  Top 30 unmatched products by row count:")
print(f"  {'PID':>10} {'Rows':>8} {'Qty':>10} {'Revenue':>14} {'First':>12} {'Last':>12} {'Cities':>6} {'Months':>6} {'Class'}")
for _, row in unmatched_detail.head(30).iterrows():
    print(f"  {int(row['product_id']):>10} {int(row['total_rows']):>8,} {int(row['total_qty']):>10,} {row['total_revenue']:>14,.0f} {str(row['first_date']):>12} {str(row['last_date']):>12} {int(row['num_cities']):>6} {int(row['num_months']):>6} {row['classification']}")

# Save unmatched detail to a small CSV report
unmatched_report_path = REPORT_DIR / "unmatched_product_detail.csv"
unmatched_detail.to_csv(unmatched_report_path, index=False)
print(f"\n  Full unmatched detail saved: {unmatched_report_path}")

results["phase5_unmatched"] = phase5

# ============================================================
# PHASE 6 — CROSS-CHECK UNMATCHED IDs vs BOTH MASTERS
# ============================================================
print("\n" + "=" * 70)
print("PHASE 6 — UNMATCHED IDs vs RAW & CLEAN MASTERS")
print("=" * 70)

phase6 = {}

unmatched_id_list = set(unmatched_detail["product_id"].astype(int).tolist())

found_in_raw   = unmatched_id_list & raw_ids
found_in_clean = unmatched_id_list & clean_ids

phase6["unmatched_ids_checked"]     = len(unmatched_id_list)
phase6["found_in_raw_master"]       = len(found_in_raw)
phase6["found_in_clean_master"]     = len(found_in_clean)
phase6["not_found_anywhere"]        = len(unmatched_id_list - raw_ids - clean_ids)

print(f"  Unmatched IDs checked:        {phase6['unmatched_ids_checked']:,}")
print(f"  Found in RAW master:          {phase6['found_in_raw_master']}")
print(f"  Found in CLEAN master:        {phase6['found_in_clean_master']}")
print(f"  Not found in ANY master:      {phase6['not_found_anywhere']:,}")

if found_in_raw:
    phase6["found_in_raw_list"] = sorted(found_in_raw)[:50]
    print(f"  !! IDs found in RAW (sample): {phase6['found_in_raw_list'][:20]}")
if found_in_clean:
    phase6["found_in_clean_list"] = sorted(found_in_clean)[:50]
    print(f"  !! IDs found in CLEAN (sample): {phase6['found_in_clean_list'][:20]}")

# ID range check
unmatched_min = min(unmatched_id_list)
unmatched_max = max(unmatched_id_list)
phase6["unmatched_min_id"] = unmatched_min
phase6["unmatched_max_id"] = unmatched_max
phase6["above_raw_max"]    = len([x for x in unmatched_id_list if x > phase2["max_product_id"]])

print(f"\n  Unmatched ID range: {unmatched_min} – {unmatched_max}")
print(f"  Master ID range:   {phase2['min_product_id']} – {phase2['max_product_id']}")
print(f"  Unmatched above master max: {phase6['above_raw_max']}")

results["phase6_crosscheck"] = phase6

# ============================================================
# PHASE 7 — PRODUCT ATTRIBUTE RECOVERABILITY
# ============================================================
print("\n" + "=" * 70)
print("PHASE 7 — PRODUCT ATTRIBUTE RECOVERABILITY")
print("=" * 70)

phase7 = {}

# Check brand/manufacturer recoverability from existing product master
# Approach: For the 1,496 unmatched IDs, can we deterministically
# recover attributes from the existing product master?
# Since they don't exist in any master, the answer is NO for direct lookup.

phase7["unmatched_direct_recovery"] = "NOT_POSSIBLE - IDs absent from all product masters"

# Check within the EXISTING product master for missing attributes
# that CAN be recovered
brand_missing    = clean_prod[clean_prod["brand_name"].isna() | (clean_prod["brand_name"] == "NOT_AVAILABLE")]
mfg_missing      = clean_prod[clean_prod["manufacturer_name"].isna() | (clean_prod["manufacturer_name"] == "NOT_AVAILABLE")]

phase7["clean_master_brand_missing"]  = len(brand_missing)
phase7["clean_master_mfg_missing"]    = len(mfg_missing)

# Check if product_name text can help recover brand for missing records
# Look for products where brand_name = NOT_AVAILABLE but product_name contains
# a known brand from the existing data
known_brands = set(
    clean_prod.loc[
        (clean_prod["brand_name"].notna()) &
        (clean_prod["brand_name"] != "NOT_AVAILABLE"),
        "brand_name"
    ].str.strip().str.upper().unique()
)
phase7["known_unique_brands"] = len(known_brands)

# Check fill_source to understand what was already recovered
fs = clean_prod["fill_source"].value_counts().to_dict()
phase7["fill_source_distribution"] = {str(k): int(v) for k, v in fs.items()}

# For unmatched products: Can ANY attributes be recovered?
# Since they're absent from the master, the only recovery path would be
# if other sales rows for the same product have different metadata
# (which shouldn't happen in a left-join, but let's verify)

print(f"  Unmatched IDs direct recovery:   {phase7['unmatched_direct_recovery']}")
print(f"  Existing clean master:")
print(f"    Brand NOT_AVAILABLE/missing:    {phase7['clean_master_brand_missing']:,}")
print(f"    Manufacturer NOT_AVAILABLE/missing: {phase7['clean_master_mfg_missing']:,}")
print(f"    Known unique brands:           {phase7['known_unique_brands']:,}")
print(f"  fill_source distribution:")
for k, v in phase7["fill_source_distribution"].items():
    print(f"    {k:30s}  {v:,}")

# Category hierarchy consistency check within existing master
print("\n  Category hierarchy consistency check...")
cat_consistency = {}
# Check if l0 → l1 mapping is deterministic
l0_l1 = clean_prod.groupby("l0_category")["l1_category"].nunique()
non_deterministic_l0_l1 = l0_l1[l0_l1 > 1]
cat_consistency["l0_to_l1_total_l0"] = len(l0_l1)
cat_consistency["l0_to_l1_non_deterministic"] = len(non_deterministic_l0_l1)

l1_l2 = clean_prod.groupby("l1_category")["l2_category"].nunique()
non_deterministic_l1_l2 = l1_l2[l1_l2 > 1]
cat_consistency["l1_to_l2_total_l1"] = len(l1_l2)
cat_consistency["l1_to_l2_non_deterministic"] = len(non_deterministic_l1_l2)

# Brand → manufacturer consistency
brand_mfg = clean_prod.dropna(subset=["brand_name", "manufacturer_name"])
brand_mfg = brand_mfg[
    (brand_mfg["brand_name"] != "NOT_AVAILABLE") &
    (brand_mfg["manufacturer_name"] != "NOT_AVAILABLE")
]
brand_to_mfg = brand_mfg.groupby("brand_name")["manufacturer_name"].nunique()
multi_mfg_brands = brand_to_mfg[brand_to_mfg > 1]
cat_consistency["brand_to_mfg_total_brands"] = len(brand_to_mfg)
cat_consistency["brand_to_mfg_non_deterministic"] = len(multi_mfg_brands)

phase7["category_consistency"] = cat_consistency

print(f"    L0→L1 mapping: {cat_consistency['l0_to_l1_total_l0']} L0 categories, "
      f"{cat_consistency['l0_to_l1_non_deterministic']} non-deterministic")
print(f"    L1→L2 mapping: {cat_consistency['l1_to_l2_total_l1']} L1 categories, "
      f"{cat_consistency['l1_to_l2_non_deterministic']} non-deterministic")
print(f"    Brand→Mfg mapping: {cat_consistency['brand_to_mfg_total_brands']} brands, "
      f"{cat_consistency['brand_to_mfg_non_deterministic']} map to multiple manufacturers")

if len(non_deterministic_l0_l1) > 0:
    print(f"\n    Non-deterministic L0→L1 examples:")
    for l0, count in non_deterministic_l0_l1.head(5).items():
        l1_vals = clean_prod[clean_prod["l0_category"] == l0]["l1_category"].unique()[:5]
        print(f"      {l0}: {list(l1_vals)}")

results["phase7_recoverability"] = phase7

# ============================================================
# SAVE INTERMEDIATE RESULTS
# ============================================================
results_path = REPORT_DIR / "audit_phase_1_to_7_results.json"

# Convert non-serializable types
def make_serializable(obj):
    if isinstance(obj, dict):
        return {str(k): make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)

with open(results_path, "w") as f:
    json.dump(make_serializable(results), f, indent=2)

print(f"\n\nPhase 1–7 results saved to: {results_path}")

con.close()

print("\n" + "=" * 70)
print("PHASES 1–7 COMPLETE")
print("=" * 70)
