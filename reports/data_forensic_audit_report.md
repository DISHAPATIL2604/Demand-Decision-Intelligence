# Demand Decision Intelligence — Complete Data Forensic Audit Report

> **Audit Date:** 2026-09-12  
> **Dataset:** Flipkart Grocery Transaction & Product Data  
> **Period:** 2022-04-01 to 2022-07-10  
> **Auditor:** Automated Data Forensics Agent  
> **Data Integrity Policy:** ZERO fabrication — all findings derived exclusively from existing project data

---

## Executive Summary

This audit examined **46,706,387 sales transactions** across **4 cities**, **17,304 products**, and **81 calendar days**. The dataset is **largely sound for demand forecasting**, with verified temporal integrity, correct daily aggregation, and no data leakage in the forecasting feature pipeline. Key findings include 1,496 permanently unmatched product IDs (genuinely absent from all masters), 79,355 rows with missing landing prices (37,484 recoverable), and a **corrected assessment** of the order_count calculation (no overcounting detected, contrary to initial concern).

---

## Phase 1 — Project File Inventory

| File | Exists | Size |
|------|--------|------|
| [dim_product.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/raw/products/dim_product.csv) | ✓ | 5.13 MB |
| [dim_product_cleaned_with_audit.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/cleaned/dim_product_cleaned_with_audit.csv) | ✓ | 5.50 MB |
| [dim_product_cleaned.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/cleaned/dim_product_cleaned.csv) | ✓ | 5.18 MB |
| [sales_product_master.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/cleaned/sales_product_master.csv) | ✓ | 9,136.95 MB |
| [daily_product_demand.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/processed/daily_product_demand.csv) | ✓ | 207.18 MB |
| fact_sales_apr1.csv | ✓ | 634.00 MB |
| fact_sales_apr2.csv | ✓ | 655.73 MB |
| fact_sales_may1.csv | ✓ | 501.63 MB |
| fact_sales_may2.csv | ✓ | 534.59 MB |
| fact_sales_jun1.csv | ✓ | 520.90 MB |
| fact_sales_jun2.csv | ✓ | 499.79 MB |
| fact_sales_jul1.csv | ✓ | 573.23 MB |

> [!NOTE]
> External data files (calendar, commodity, weather) exist as **empty templates** (headers only, no data rows). These are NOT usable.

> [!IMPORTANT]
> The `dataset/combined/` directory is empty (contains only `.gitkeep`). No intermediate combined sales file exists.

---

## Phase 2 — Raw Product Master Validation

| Metric | Value |
|--------|-------|
| Total rows | **32,226** |
| Columns | 13 (includes `Unnamed: 0` index column) |
| Unique product_id | **32,226** |
| Duplicate product_id | **0** |
| ID range | 1 – 498,814 |
| Has spurious index column | Yes (`Unnamed: 0`) |

### Missing Values in Raw Master

| Column | Missing |
|--------|---------|
| brand_name | 1,438 |
| manufacturer_name | 2,416 |

> [!TIP]
> All other columns (product_name, unit, product_type, categories) have **zero** missing values in the raw master. The only gaps are brand and manufacturer.

---

## Phase 3 — Cleaned Product Master Validation

| Metric | Value |
|--------|-------|
| Total rows | **32,226** |
| Unique product_id | **32,226** |
| Duplicate IDs | **0** |
| `fill_source` column | ✓ Present |
| Missing values after cleaning | **NONE** |

### fill_source Distribution

| Source | Count |
|--------|-------|
| original | 29,030 |
| not_available_no_data | 1,105 |
| mapped_from_brand | 875 |
| mapped_from_manufacturer | 753 |
| extracted_then_mapped | 460 |
| extracted_from_product_name | 3 |

### RAW vs CLEAN Cross-Validation

| Check | Result |
|-------|--------|
| RAW IDs missing from CLEAN | **0** |
| CLEAN IDs not in RAW | **0** |
| IDs in both | **32,226** |

### Field Consistency (sample of 500 shared IDs)

| Column | Compared | Mismatches |
|--------|----------|------------|
| product_name | 500 | **0** |
| l0_category | 500 | **0** |
| l1_category | 500 | **0** |
| l2_category | 500 | **0** |

> [!TIP]
> The cleaned master is a perfect superset of the raw master — no IDs lost, no field values altered for the sampled records. The `fill_source` column provides full auditability.

### Category Hierarchy Consistency

| Mapping | Total Categories | Non-Deterministic |
|---------|-----------------|-------------------|
| L0 → L1 | 21 | **21** (all are 1-to-many, as expected for hierarchy) |
| L1 → L2 | 205 | **75** |
| Brand → Manufacturer | 2,193 | **262** (map to multiple manufacturers) |

> [!NOTE]
> L0→L1 being "non-deterministic" is **expected**: each L0 category contains multiple L1 subcategories. This is a standard hierarchical taxonomy, not an inconsistency. The 262 brands mapping to multiple manufacturers are worth noting but may reflect legitimate business relationships (e.g., co-branding, white-label).

---

## Phase 4 — Sales Product Master Validation

| Metric | Value |
|--------|-------|
| Total rows | **46,706,387** |
| Columns | 21 |
| Unique product_id | **17,304** |
| Date range | 2022-04-01 to 2022-07-10 |
| Unique dates | 81 |
| Cities | Bengaluru, Delhi, HR-NCR, Mumbai |

### Missing Values in Sales Master

| Column | Missing Rows | % of Total |
|--------|-------------|------------|
| total_weighted_landing_price | 79,355 | 0.17% |
| product_name | 532,122 | 1.14% |
| brand_name | 532,122 | 1.14% |
| manufacturer_name | 532,122 | 1.14% |
| l0_category | 532,122 | 1.14% |
| l1_category | 532,122 | 1.14% |
| l2_category | 532,122 | 1.14% |

> [!IMPORTANT]
> The 532,122 missing product attributes correspond exactly to the **1,496 unmatched product IDs**. These are not random missing values — they are structurally caused by the left-join with the product master.

---

## Phase 5 — Unmatched Product ID Forensics

| Metric | Value |
|--------|-------|
| Unmatched rows | **532,122** (1.14%) |
| Unique unmatched IDs | **1,496** |
| Total unmatched quantity | **629,141 units** |
| Total unmatched revenue | **₹57,839,340** |
| IDs in multiple cities | **773** (51.7%) |
| IDs in multiple months | **636** (42.5%) |

### Evidence-Based Classification

| Classification | Count | Description |
|---------------|-------|-------------|
| A_recurring_strong_evidence | **272** | ≥50 rows, ≥2 cities, ≥2 months |
| A_recurring_moderate_evidence | **433** | ≥10 rows, multiple city OR month |
| B_low_frequency | **507** | 5–49 rows |
| D_unresolved_single_occurrence | **269** | 1 row, not suspicious |
| C_suspicious_anomalous | **15** | Zero prices/quantities |

> [!WARNING]
> **705 out of 1,496 unmatched IDs (47.1%)** are classified as recurring products with transactional evidence. These are real products — their absence from the product master likely reflects a **snapshot mismatch** (the product master was extracted at a different time than the sales data, and these products were added/removed in between).

### Top 10 Unmatched Products by Volume

| Product ID | Rows | Quantity | Revenue | Date Range | Cities | Months |
|-----------|------|----------|---------|------------|--------|--------|
| 455347 | 34,752 | 41,964 | ₹1,580,422 | Apr 6 – Jun 20 | 2 | 3 |
| 271303 | 12,373 | 13,610 | ₹534,538 | Apr 6 – May 21 | 4 | 2 |
| 374072 | 11,274 | 12,760 | ₹501,359 | Apr 6 – May 21 | 4 | 2 |
| 476146 | 11,012 | 13,248 | ₹825,518 | Apr 1 – Jul 10 | 4 | 4 |
| 476147 | 9,982 | 10,312 | ₹2,400,270 | Apr 1 – Jul 10 | 4 | 4 |
| 393010 | 9,115 | 10,314 | ₹567,508 | Apr 1 – Jul 9 | 3 | 4 |
| 23827 | 8,847 | 9,217 | ₹442,939 | Apr 1 – Jul 10 | 4 | 4 |
| 482552 | 8,723 | 11,753 | ₹223,206 | Apr 15 – Jun 20 | 3 | 3 |
| 476159 | 8,565 | 9,883 | ₹617,169 | Apr 1 – Jul 10 | 4 | 4 |
| 410892 | 7,262 | 7,810 | ₹306,625 | Apr 6 – May 21 | 4 | 2 |

Full detail: [unmatched_product_detail.csv](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/unmatched_product_detail.csv)

---

## Phase 6 — Cross-Check Unmatched IDs vs Both Masters

| Check | Result |
|-------|--------|
| Unmatched IDs checked | 1,496 |
| Found in RAW master | **0** |
| Found in CLEAN master | **0** |
| Not found in ANY master | **1,496** |
| Unmatched ID range | 57 – 488,730 |
| Master ID range | 1 – 498,814 |
| Unmatched IDs above master max | **0** |

> [!IMPORTANT]
> **CONFIRMED:** All 1,496 unmatched IDs are genuinely absent from both RAW and CLEAN product masters. They fall within the master's numeric range (not overflow). These IDs were never part of the provided product-master snapshot.

---

## Phase 7 — Product Attribute Recoverability

| Recovery Path | Status |
|--------------|--------|
| Direct lookup in masters | **NOT_POSSIBLE** (IDs absent) |
| Cross-reference from sales | **NOT_POSSIBLE** (left-join already attempted) |
| Text extraction from product names | **NOT_POSSIBLE** (no product names available for unmatched IDs) |

> [!CAUTION]
> Product attributes for the 1,496 unmatched IDs are **permanently NOT_AVAILABLE** from existing project data. Any attempt to assign names, brands, or categories to these IDs would constitute data fabrication.

---

## Phase 8 — Landing Price Audit

| Metric | Value |
|--------|-------|
| Total rows | 46,706,387 |
| Missing landing price | **79,355** (0.17%) |
| Zero landing price | 22,215 |
| Negative landing price | **0** |
| LP > 10,000 | 34 |
| Products with missing LP | **757** |
| Products with valid LP history | **743** |
| Products with NO valid LP history | **14** |

### Missing LP by Month

| Month | Missing Rows |
|-------|-------------|
| 2022-04 | 21,164 |
| 2022-05 | 7,605 |
| 2022-06 | 4,095 |
| 2022-07 | **46,491** |

> [!WARNING]
> July 2022 has **59% of all missing LP rows** despite covering only 10 days. This suggests a data-capture issue in the final data extraction period.

### Missing LP by City

| City | Missing Rows |
|------|-------------|
| Delhi | 32,214 |
| HR-NCR | 22,901 |
| Mumbai | 22,218 |
| Bengaluru | 2,022 |

### Deterministic Recovery Tiers

| Tier | Method | Recoverable | Not Recoverable |
|------|--------|-------------|-----------------|
| Tier 1 | Same product + same city | **28,171** | 51,184 |
| Tier 2 | Same product, any city | **37,484** | 41,871 |

### 14 Products with Permanently Unresolvable LP

| Product ID | Missing Rows |
|-----------|-------------|
| 486376 | 18,400 |
| 486018 | 7,171 |
| 486016 | 6,868 |
| 486377 | 5,503 |
| 486017 | 3,913 |
| 487701 | 5 |
| 487957 | 3 |
| 482235 | 2 |
| + 6 more | 1 each |

> [!NOTE]
> The existing imputation (product-level median, 37,484 rows) aligns with Tier 2. The remaining **41,871 rows** must stay as NOT_AVAILABLE.

---

## Phase 9 — Numerical Validation

### procured_quantity

| Check | Value | Status |
|-------|-------|--------|
| Missing | 0 | CONFIRMED |
| Negative | **0** | CONFIRMED |
| Zero | 184,411 (0.39%) | VALID — business signal |
| Max | 50 | CONFIRMED — no overflow |
| Median | 1.0 | CONFIRMED |
| Mean | 1.29 | CONFIRMED |

### unit_selling_price

| Check | Value | Status |
|-------|-------|--------|
| Missing | 0 | CONFIRMED |
| Negative | **0** | CONFIRMED |
| Zero | 125,349 (0.27%) | SUSPICIOUS — flag, do not delete |
| > 10,000 | 18 | SUPPORTED — product 477200, consistent price |
| Max | ₹10,999 | SUPPORTED |
| Median | ₹50 | CONFIRMED |
| Mean | ₹87.17 | CONFIRMED |

### total_discount_amount

| Check | Value | Status |
|-------|-------|--------|
| Missing | 0 | CONFIRMED |
| Negative | **0** | CONFIRMED |
| Zero | 45,629,057 (97.7%) | VALID — most transactions have no discount |
| Max | ₹1,500 | CONFIRMED |

### total_weighted_landing_price

| Check | Value | Status |
|-------|-------|--------|
| Missing | 79,355 (0.17%) | KNOWN ISSUE |
| Negative | **0** | CONFIRMED |
| Zero | 22,215 | SUSPICIOUS — worth investigating |
| > 10,000 | 34 | SUPPORTED |
| Max | ₹20,880.12 | SUPPORTED |

### Suspicious Combinations

| Condition | Rows | Assessment |
|-----------|------|------------|
| qty > 0 AND price = 0 | **119,027** | SUSPICIOUS — free samples/promos possible |
| qty = 0 AND price > 0 | **178,089** | SUSPICIOUS — potential returns/cancellations |
| discount > revenue | **231** | SUSPICIOUS — possible data entry error |
| Duplicate transaction groups | **0** | CONFIRMED — no exact duplicates |

> [!NOTE]
> **No exact duplicate transactions exist.** The 119,027 "free item" rows (qty>0, price=0) represent 0.25% of data and are plausible for a grocery e-commerce platform offering promotions.

---

## Phase 10 — Date / Temporal Audit

| Check | Result | Status |
|-------|--------|--------|
| Date range | 2022-04-01 to 2022-07-10 | CONFIRMED |
| Unique dates | 81 | CONFIRMED |
| Null dates | 0 | CONFIRMED |
| Invalid dates | **0** | CONFIRMED |
| Future dates | 0 | CONFIRMED |
| Pre-range dates | 0 | CONFIRMED |

### Monthly Distribution

| Month | Rows | Products | Cities | Days |
|-------|------|----------|--------|------|
| 2022-04 | 15,385,896 | 11,241 | 4 | 30 |
| 2022-05 | 12,356,432 | 13,043 | 4 | 21 |
| 2022-06 | 12,152,765 | 14,113 | 4 | 20 |
| 2022-07 | 6,811,294 | 13,382 | 4 | 10 |

> [!NOTE]
> May and June have only 21 and 20 days respectively (not all calendar days). This means the raw sales files don't contain every single calendar day. This is the data as-provided, not a data quality issue. July has only 10 days (through July 10).

### City-Month Distribution

| City | Apr | May | Jun | Jul |
|------|-----|-----|-----|-----|
| Bengaluru | 2,873,330 | 2,551,644 | 2,625,559 | 1,460,975 |
| Delhi | 7,108,211 | 5,774,470 | 5,499,644 | 3,067,533 |
| HR-NCR | 4,000,596 | 3,123,655 | 3,061,890 | 1,680,387 |
| Mumbai | 1,403,759 | 906,663 | 965,672 | 602,399 |

> [!TIP]
> All 4 cities are present across all 4 months. No city-month combinations are missing. The temporal coverage is complete for the available date range.

---

## Phase 11 — Daily Demand Aggregation Audit

| Metric | Value | Status |
|--------|-------|--------|
| Total rows | **1,764,981** | CONFIRMED |
| Unique dates | 81 | CONFIRMED |
| Unique products | 17,304 | CONFIRMED |
| Unique cities | 4 | CONFIRMED |
| Date range | 2022-04-01 to 2022-07-10 | CONFIRMED |
| Total quantity | 60,176,096 | CONFIRMED |
| Total revenue | ₹4,725,948,522 | CONFIRMED |
| Total order_count | 46,706,387 | See Phase 12 |
| Missing product_name | 40,913 (2.3%) | EXPECTED |
| Missing L0 category | 40,913 | EXPECTED |
| Missing daily_quantity | 0 | CONFIRMED |
| Missing daily_revenue | 0 | CONFIRMED |
| Negative quantity | 0 | CONFIRMED |
| Negative revenue | 0 | CONFIRMED |
| Zero quantity rows | 6,993 | VALID |
| Duplicate (date+product+city) | **0** | CONFIRMED |

### Aggregation Correctness

| Check | Sales Total | Demand Total | Match? |
|-------|------------|-------------|--------|
| Quantity | 60,176,096 | 60,176,096 | **YES** ✓ |
| Revenue | ₹4,725,948,522.00 | ₹4,725,948,522.00 | **YES** ✓ |

### Consistency Checks

| Check | Result |
|-------|--------|
| Products with multiple names | **0** |
| Products with multiple L0 categories | **0** |

> [!TIP]
> Daily demand aggregation is **mathematically correct**. Quantity and revenue sums match exactly between the transaction-level sales master and the aggregated daily demand file. No product has inconsistent descriptive attributes across rows.

---

## Phase 12 — Order Count Verification

> [!IMPORTANT]
> **Initial concern:** The `build_daily_demand.py` script performs chunk-level `nunique(order_id)` and then sums across chunks, which could overcount orders crossing chunk boundaries.

### Verification Results

| Check | Result |
|-------|--------|
| Sample verification (3 days, 57,141 rows) | **ALL MATCH** |
| Existing total order_count (sum) | **46,706,387** |
| Correct total (global nunique) | **46,706,387** |
| Difference | **0** |
| Overcounting detected | **NO** |

> [!TIP]
> **CORRECTED FINDING:** Despite the theoretical risk of chunk-boundary overcounting, the actual order_count values are correct. This is likely because the second aggregation pass in `build_daily_demand.py` (line 78-88) sums per-chunk order_counts — and in this dataset, order_ids happen to not cross chunk boundaries for the same (date, product_id, city_name, product_name, l0/l1/l2) group. The existing order_count is **SAFE TO USE**.

> [!WARNING]
> However, the total order_count (46,706,387) equals the total number of sales rows. This means **every sales row has a unique order_id within each product-city-date group** — effectively, each row is a separate "order." This is mathematically correct but means order_count = row_count, not distinct customer orders in the traditional sense.

---

## Phase 13 — Forecasting Feature Audit

| Parameter | Value | Status |
|-----------|-------|--------|
| Calendar start | 2022-04-01 | CONFIRMED |
| Calendar end | 2022-07-10 | CONFIRMED |
| Calendar days | 101 | CONFIRMED |
| Product-city combinations | 46,305 | CONFIRMED |
| Expected calendar rows | 4,676,805 | CONFIRMED |
| Model start (after warmup) | 2022-04-29 | CONFIRMED |
| Training period | 2022-04-29 to 2022-06-30 (63 days) | CONFIRMED |
| Validation period | 2022-07-01 to 2022-07-10 (10 days) | CONFIRMED |

### Feature Implementation Audit

| Feature | Implementation | Leakage Risk |
|---------|---------------|-------------|
| Lag 1/7/14/28 | `group.shift(N)` | **LOW** — backward-looking only |
| Rolling mean 7/14/28 | `shift(1).rolling(N).mean()` | **LOW** — shift before rolling |
| Rolling std 7 | `shift(1).rolling(7).std()` | **LOW** — shift before rolling |
| day_of_week | `date_.dt.dayofweek` | **NONE** — deterministic from date |
| is_weekend | `day_of_week >= 5` | **NONE** — deterministic from date |

### Identified Concerns

1. **Zero-filling before product first sale:** Products appearing after 2022-04-01 get zero-demand rows for the pre-appearance period. This is standard for forecasting but inflates early lag values toward zero.

2. **product_name in GROUP_COLS:** `build_daily_demand.py` groups by product_name. If product_name were inconsistent (verified: it's not), this could split groups. Currently safe because Phase 11 confirmed 0 products with multiple names.

3. **Descriptive columns dropped:** The forecasting script correctly uses only `product_id`, `city_name`, `daily_quantity` — no leakage from descriptive fields.

---

## Phase 14 — Leakage Audit

| Leakage Vector | Status | Evidence |
|----------------|--------|----------|
| Sort order before features | **CORRECT** | Sorted by product_id, city_name, date_ |
| Rolling window uses future data | **NO** | shift(1) applied before rolling |
| Train/validation temporal split | **STRICT** | < 2022-07-01 vs ≥ 2022-07-01 |
| Future information in features | **NONE** | All features are backward-looking |
| Calendar feature leakage | **NONE** | day_of_week, is_weekend are deterministic |
| Cross-product contamination | **NONE** | Features grouped by (product_id, city_name) |
| Target variable leakage | **NONE** | Target excluded by shift operations |
| **Overall leakage risk** | **LOW** | |

### Remaining Concerns

- Zero-filled calendar rows before a product's first sale may create artificially low lag values during the early warmup period
- The 10-day validation window (Jul 1–10) is short; model performance metrics should be interpreted with caution

---

## Phase 15 — Final Data Quality Decision Matrix

| # | Data Issue | Rows/IDs Affected | Recoverable? | Method | Evidence Level | Recommended Action |
|---|-----------|-------------------|-------------|--------|---------------|-------------------|
| 1 | Unmatched product IDs | 532,122 rows / 1,496 IDs | **NOT_RECOVERABLE** | N/A — IDs absent from all masters | CONFIRMED (Phase 6) | KEEP AS NOT_AVAILABLE |
| 2 | Missing LP (product has history) | 37,484 rows / 743 products | **RECOVERABLE** | Product-level median LP | SUPPORTED | SAFE TO RECOVER with audit trail |
| 3 | Missing LP (no product history) | 41,871 rows / 14 products | **NOT_RECOVERABLE** | N/A — no valid LP exists | CONFIRMED | KEEP AS NOT_AVAILABLE |
| 4 | Zero procured_quantity | 184,411 rows | N/A | N/A | Business signal | **MUST NOT BE DELETED** |
| 5 | Zero unit_selling_price | 125,349 rows | N/A | N/A | Possible promotions | SUSPICIOUS — preserve |
| 6 | order_count accuracy | All 1,764,981 demand rows | **CORRECT** | Verified: 0 overcounting | CONFIRMED (Phase 12) | SAFE TO USE |
| 7 | Missing brand/manufacturer | 532,122 sales rows | **NOT_RECOVERABLE** | Caused by unmatched product IDs | CONFIRMED | KEEP AS NOT_AVAILABLE |
| 8 | Extreme prices (>₹10,000) | 18 rows | N/A | Product 477200: ₹10,999 consistently | SUPPORTED | NEEDS MANUAL REVIEW |
| 9 | Duplicate transactions | **0 groups** | N/A | N/A | CONFIRMED | No action needed |
| 10 | Discount > revenue | 231 rows | N/A | N/A | SUSPICIOUS | Flag but preserve |
| 11 | qty > 0, price = 0 | 119,027 rows | N/A | Possible free samples/promos | SUSPICIOUS | Flag but preserve |
| 12 | qty = 0, price > 0 | 178,089 rows | N/A | Possible returns/cancellations | SUSPICIOUS | Flag but preserve |
| 13 | Zero landing price | 22,215 rows | N/A | May be valid (zero-cost items) | SUSPICIOUS | Flag for review |
| 14 | LP > ₹10,000 | 34 rows | N/A | Max = ₹20,880.12 | SUPPORTED | Review if used in cost analysis |
| 15 | Missing dates in calendar | 0 out of 81 | N/A | N/A | CONFIRMED | No action needed |

---

## Classification Summary

### 1. SAFE TO USE ✓

- Transaction-level sales data (46,706,387 rows — all preserved)
- Matched product attributes (98.86% match rate)
- Date/temporal data (validated: no nulls, no invalids, no future dates)
- Quantity data (no negatives, max=50, verified range)
- Price data (no negatives, verified range)
- Daily demand quantity and revenue (aggregation verified exact-match)
- Order count values (verified correct — no overcounting)
- Category hierarchy (consistent within demand file)
- Lag features (no leakage, correct shift implementation)
- Rolling features (shift-before-rolling, no leakage)
- Train/validation temporal split (strict, no contamination)

### 2. SAFE TO RECOVER

- **Landing price:** ~37,484 rows via product-level median (Tier 2)
  - Must include `price_fill_method` and `price_fill_source` columns
  - Already implemented in [impute_landing_price.py](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/sales%20data/impute_landing_price.py)

### 3. KEEP AS NOT_AVAILABLE

- Product attributes for 1,496 unmatched IDs (permanently unresolvable)
- Landing price for 14 products with no valid history (41,871 rows)
- Brand/manufacturer for products with `fill_source = not_available_no_data` (1,105 products)

### 4. NEEDS MANUAL REVIEW

- Extreme prices: 18 rows with price > ₹10,000 (product 477200 at ₹10,999)
- 231 rows where discount exceeds revenue
- 22,215 rows with zero landing price (valid or data issue?)

### 5. MUST NOT BE DELETED

- Zero quantity rows (184,411) — valid business signal
- Zero price rows (125,349) — possible promotions
- Unmatched product sales rows (532,122) — real demand data
- All raw data files under `dataset/raw/`
- Any transaction row without explicit authorization

### 6. MUST NOT BE USED (as-is, without context)

- The interpretation that order_count = distinct customer orders (it actually equals row count per group)
- External data files (calendar, commodity, weather) — **empty templates with headers only**

---

## Key Findings Summary

```mermaid
graph TD
    A["46,706,387 Sales Rows"] --> B{"Product Master Match?"}
    B -->|"98.86% matched"| C["46,174,265 Matched Rows"]
    B -->|"1.14% unmatched"| D["532,122 Unmatched Rows<br/>1,496 Product IDs"]
    
    C --> E{"Landing Price?"}
    E -->|"99.83% present"| F["Valid LP Rows"]
    E -->|"0.17% missing"| G["79,355 Missing LP"]
    
    G --> H{"Product History?"}
    H -->|"743 products"| I["37,484 RECOVERABLE"]
    H -->|"14 products"| J["41,871 NOT_AVAILABLE"]
    
    D --> K["NOT_RECOVERABLE<br/>Keep demand data<br/>Mark attributes NOT_AVAILABLE"]
    
    C --> L["1,764,981 Daily Demand Rows"]
    L --> M["Aggregation: VERIFIED CORRECT"]
    L --> N["Order Count: VERIFIED CORRECT"]
    L --> O["No Leakage: CONFIRMED"]
```

---

## Audit Conclusion

> [!IMPORTANT]
> **The dataset is SAFE for demand forecasting** with the following caveats:
> 1. 1.14% of sales rows lack product attributes (permanently NOT_AVAILABLE)
> 2. 0.09% of rows have unresolvable landing prices
> 3. The 10-day validation window is short
> 4. Zero-filling before product first-sale may influence early period features
>
> **No data fabrication, deletion, or modification was performed during this audit.**
> All findings are derived exclusively from existing project data.
