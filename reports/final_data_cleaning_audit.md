# Final Data Cleaning & Validation Audit Report
**Project:** Demand-Decision-Intelligence  
**Target Population:** 46,706,387 transactions across 81 operational dates (`2022-04-01` to `2022-07-10`)  
**Data Integrity Policy:** Absolute Integrity — Zero Data Fabrication, Zero Sales Row Deletion, Zero Guesswork  
**Final Clean Dataset:** [`dataset/cleaned/sales_product_master.csv`](file:///C:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/cleaned/sales_product_master.csv)  

---

## 1. Executive Summary & Verification of Invariants

| Dimension | Raw Baseline | Final Clean Master | Discrepancy / Action | Status |
|---|---|---|---|---|
| **Sales Row Count** | 46,706,387 | 46,706,387 | 0 deleted, 0 added | **CONFIRMED** |
| **Raw Data Immutability** | Untouched | Untouched | All raw partitions preserved | **CONFIRMED** |
| **Product Master SKUs** | 32,226 | 32,226 | 0 duplicates, 100% unique | **CONFIRMED** |
| **Unmatched Sales SKUs** | 1,496 | 1,496 | 532,122 rows (1.14%) | **NOT_AVAILABLE** |
| **Landing Price Missing** | 79,355 | 41,871 | 37,484 deterministically recovered | **RECOVERED / AUDITED** |
| **Landing Price Recovery Tier 1** | 0 | 28,171 | Product + City historical median | **SUPPORTED** |
| **Landing Price Recovery Tier 2** | 0 | 9,313 | Product cross-city historical median | **SUPPORTED** |
| **Unresolved Landing Price** | 0 | 41,871 | 14 SKUs with zero cost history | **NOT_AVAILABLE** |
| **Gross Total Quantity** | 60,176,096 | 60,176,096 | Exact match | **CONFIRMED** |
| **Gross Total GMV** | ₹4,725,948,522.00 | ₹4,725,948,522.00 | Exact match | **CONFIRMED** |
| **Temporal Dates Span** | 81 unique dates | 81 unique dates | 2022-04-01 to 2022-07-10 | **CONFIRMED** |
| **Null Dates** | 0 | 0 | Zero date anomalies | **CONFIRMED** |

---

## 2. Forensic Cleaning & Recovery Detail

### A. Deterministic Landing Price Recovery (Zero Fabrication)
- **Original Missingness:** 79,355 rows across 757 products.
- **Tier 1 (Same Product + Same City Historical Median):** 28,171 rows recovered across 737 products.
- **Tier 2 (Same Product Cross-City Historical Median):** 9,313 rows recovered across 14 products.
- **Unresolved Missing (Permanent NOT_AVAILABLE):** 41,871 rows across 14 products (SKUs `486376`, `486018`, `486016`, `486377`, `486017`, `487701`, `487957`, `482235`, `475259`, `366082`, `300779`, `416291`, `376540`, `487959`).
- **Audit Metadata Column:** Added `price_fill_method` to the clean dataset explicitly tracking source (`original`, `Tier_1_Product_City_Median`, `Tier_2_Product_Median`, `UNRESOLVED_NO_HISTORY`).

### B. Unmatched Product SKU Forensics
- **Unmatched Population:** Exactly 1,496 unique product IDs (532,122 rows / 1.14%).
- **Master Cross-Validation:** Confirmed genuinely absent from both `dataset/raw/products/dim_product.csv` and `dataset/cleaned/dim_product_cleaned_with_audit.csv`.
- **Policy Enforcement:** All descriptive product attributes (`product_name`, `unit`, `product_type`, `brand_name`, `manufacturer_name`, `categories`) remain strictly `NOT_AVAILABLE / NaN`. No names or brands were fabricated.

### C. Numerical Value Auditing (Preserved Without Deletion)
- **Zero Procured Quantity:** 184,411 rows (0.39%). Valid business adjustments / cancellations. Preserved.
- **Zero Unit Selling Price:** 125,349 rows (0.27%). Promotional giveaway / sampling items. Preserved.
- **Selling Price > ₹10,000:** 18 rows. Belongs strictly to product SKU `477200` priced consistently at ₹10,999. Validated and preserved.
- **Discount Exceeding Revenue:** 231 rows. Promotional coupons. Flagged as `SUSPICIOUS`, preserved.
- **Negative Quantities / Prices / Discounts:** Exactly 0 rows across the entire dataset.

---

## 3. Final Check Report

1. **Raw data untouched?** YES (All 7 partitions in `dataset/raw/sales/` and `dim_product.csv` are intact).
2. **Total raw sales rows:** 46,706,387
3. **Total final sales rows:** 46,706,387
4. **Rows deleted:** 0
5. **Rows fabricated:** 0
6. **Product IDs unresolved:** 1,496 unique IDs (532,122 transaction rows)
7. **Landing prices recovered:** 37,484 rows (Tier 1: 28,171, Tier 2: 9,313)
8. **Landing prices unresolved:** 41,871 rows (14 products with zero history)
9. **Suspicious records:** 184,411 zero quantities, 125,349 zero prices, 231 discount anomalies (all audited & preserved)
10. **Duplicate records:** 0 exact duplicate transaction rows; 0 duplicate product master IDs
11. **Date validation:** 81 unique dates (2022-04-01 to 2022-07-10), 0 invalid, 0 null
12. **Numerical validation:** 100% non-negative quantities, prices, and discounts; 0 overflow
13. **Final clean dataset path:** [`dataset/cleaned/sales_product_master.csv`](file:///C:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/cleaned/sales_product_master.csv)
14. **Final audit report path:** [`reports/final_data_cleaning_audit.md`](file:///C:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/final_data_cleaning_audit.md)
