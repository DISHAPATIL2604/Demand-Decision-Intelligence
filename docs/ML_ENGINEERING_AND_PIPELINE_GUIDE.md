# ML Engineering & End-to-End Pipeline Guide
**Project:** Demand-Decision-Intelligence  
**Dataset:** Flipkart Supermart Indian Grocery Transaction & Product Data  
**Pipeline Status:** Production-Ready & Audited  

---

## 1. Data Sources & Architecture

The system operates on physical grocery transaction data without external web, API, or synthetic data fabrication:
- **Raw Transaction Partitions:** `dataset/raw/sales/fact_sales_*.csv` (7 monthly chunks, 46,706,387 transactions).
- **Product Master:** `dataset/raw/products/dim_product.csv` (32,226 SKUs).
- **Cleaned Product Master:** `dataset/cleaned/dim_product_cleaned_with_audit.csv` (32,226 SKUs with auditable `fill_source` column).
- **Sales Master:** `dataset/cleaned/sales_product_master.csv` (46,706,387 rows, 17,304 active selling SKUs).
- **Daily Aggregated Demand:** `dataset/processed/daily_product_demand.csv` (1,764,981 daily grain rows).

---

## 2. Data Transformations & Audit Decisions

### A. Landing Price Recovery (Zero Fabrication)
- **Total Missing Records:** 79,355 rows (0.17% of transactions) across 757 products.
- **Deterministic Recovery:**
  - **Tier 1 (Same Product + Same City Historical Median):** 28,171 rows recovered across 737 products.
  - **Tier 2 (Same Product Cross-City Historical Median):** 9,313 rows recovered across 14 products.
  - **Total Recovered:** Exactly 37,484 rows.
- **Unresolved Missing:** Exactly 41,871 rows across 14 products (e.g. SKUs `486376`, `486018`, `486016`, `486377`, `486017`) have zero landing price records in the entire dataset. In accordance with zero-fabrication policy, they remain `NOT_AVAILABLE / NaN` and are never filled with global means.
- **Audit Table:** Generated at [`reports/landing_price_recovery_audit.csv`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/landing_price_recovery_audit.csv) and [`dataset/processed/landing_price_recovery_lookup.csv`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/dataset/processed/landing_price_recovery_lookup.csv).

### B. Unmatched Product SKUs
- **Unmatched Dimensions:** 1,496 unique IDs representing 532,122 sales transactions (1.14%).
- **Verification:** All 1,496 IDs are absent from both RAW and CLEAN product masters; all IDs are valid numeric values (`57` to `488,730`).
- **Forensic Policy:** Demand transactions are retained for sales and demand forecasting. Categorical attributes are strictly marked as `NOT_AVAILABLE`. No product names, brands, or manufacturers are inferred.

### C. Daily Demand Aggregation
- **Grain:** `(date_, product_id, city_name, product_name, l0_category, l1_category, l2_category)`.
- **Integrity Validation:** Total quantity (`60,176,096`) and total revenue (`₹4,725,948,522.00`) match the transaction sales master with zero discrepancy.
- **Order Count Semantic:** Represents line-item transaction count (not multi-product customer baskets).

---

## 3. Feature Engineering & Leakage Prevention

The feature generation pipeline (`forecasting/forecast_pipeline.py`) creates a complete calendar grid across all 46,305 product-city series from `2022-04-01` to `2022-07-10` (101 calendar days = 4,676,805 total rows).

### Strict Anti-Leakage Design:
1. **Window Shifts:** All lag features (`lag_1`, `lag_7`, `lag_14`, `lag_28`) use historical lags only (`LAG(daily_quantity, k)`).
2. **Rolling Windows:** All rolling statistics (`rolling_mean_7`, `rolling_mean_14`, `rolling_mean_28`, `rolling_std_7`) are computed over `ROWS BETWEEN k PRECEDING AND 1 PRECEDING`, strictly excluding the target day $t$.
3. **Calendar Features:** `day_of_week` (0 to 6) and `is_weekend` (0 or 1) are deterministic calendar features.
4. **Warmup Truncation:** The first 28 calendar days are discarded to ensure zero null feature values. Model data starts on `2022-04-29` (3,380,265 rows).

---

## 4. Forecasting Model Benchmarks & Evaluation

Evaluation is strictly chronological:
- **Training Set:** `2022-04-29` to `2022-06-30` (63 calendar days, 2,917,215 rows).
- **Validation Set:** `2022-07-01` to `2022-07-10` (10 calendar days, 463,050 rows).

### Benchmark Comparison:
| Model Type | Model Name | MAE | RMSE | WAPE (%) | Training Time |
|---|---|---|---|---|---|
| Baseline | Naive (Lag-1) | 5.9480 | 45.6442 | 32.43% | Instant |
| Baseline | Seasonal Naive (Lag-7) | 14.5525 | 105.8495 | 79.35% | Instant |
| Baseline | Rolling Mean 7 | 9.1043 | 70.4306 | 49.64% | Instant |
| **ML Model** | **Ridge Regression** | **5.8639** | **41.0083** | **31.97%** | **0.31s** |
| ML Model | HistGradientBoosting (GBT) | 7.4838 | 73.9660 | 40.81% | 3.64s |

**Key Finding:** Ridge Regression achieved the lowest WAPE (31.97%) and lowest RMSE (41.01). Seasonal Naive (Lag-7) performed poorly (79.35% WAPE) due to intra-week volatility and promotional spikes in grocery sales.

---

## 5. Error Analysis & Diagnostics

1. **Regional Performance:**
   - **Bengaluru:** 1,768,605 units | WAPE: 38.68% | MAE: 6.52
   - **Delhi:** 3,860,573 units | WAPE: 39.77% | MAE: 12.80
   - **HR-NCR:** 2,106,691 units | WAPE: 42.63% | MAE: 7.02
   - **Mumbai:** 756,445 units | WAPE: 45.98% | MAE: 3.15
2. **Intermittent Demand vs Regular Demand:**
   - **Regular / Frequent Series (26,015 series):** 8,437,729 units | **WAPE: 38.18%**.
   - **Sparse / Intermittent Series (20,290 series):** 54,585 units | **WAPE: 446.34%**.
   - *Diagnostic:* High WAPE in sparse series is mathematically expected because dividing small absolute errors by near-zero volume inflates percentage metrics. For intermittent items, Croston or Poisson inventory models should be applied.
3. **High-Volume Error Outliers:** Concentrated in staple SKUs in Delhi and HR-NCR (e.g. SKUs `19512`, `12872`, `391306`) where demand surged sharply above the historical 30-day baseline in early July.

---

## 6. Inventory Decision Layer

Implements dynamic inventory replenishment policies across all 38,936 active series (`inventory/inventory_decision_engine.py`):
- **Safety Stock ($SS$):**
  $$SS = \lceil Z \times \sigma_d \times \sqrt{L} \rceil$$
- **Reorder Point ($ROP$):**
  $$ROP = \lceil (\mu_d \times L) + SS \rceil$$
- **Target Stock Level ($S_{target}$):**
  $$S_{target} = \lceil \mu_d \times (L + R) + SS \rceil$$

### Source Data vs Configuration Parameters:
- **Derived from Source Data:** Mean daily demand ($\mu_d$), daily demand standard deviation ($\sigma_d$), unit landing price ($C_{unit}$).
- **Configurable Parameters (`NOT_AVAILABLE` in raw data):**
  - Supplier Lead Time ($L$): default 3 days.
  - Target Service Level ($\alpha$): default 95% ($Z = 1.645$).
  - Review Period ($R$): default 7 days.
  - On-hand Inventory ($I_{on\_hand}$): uploadable via ERP/WMS.

---

## 7. Backend API Endpoints

The FastAPI backend exposes the following endpoints under `/api/v1/demand`:
- `GET /api/v1/demand/summary`: Catalog size, total units, gross GMV, date span, and match statistics.
- `GET /api/v1/demand/forecast-metrics`: Live model comparison metrics (MAE, RMSE, WAPE) and error analysis.
- `GET /api/v1/demand/inventory-recommendations`: Parameterized inventory policy recommendations (supports filtering by city, custom lead time, and service level).
