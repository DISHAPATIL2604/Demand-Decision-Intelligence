# Exploratory Data Analysis (EDA) Report
**Project:** Demand-Decision-Intelligence  
**Dataset:** Flipkart Supermart Indian Grocery Sales & Product Catalog  
**Data Scope:** 46,706,387 transactions | 81 active operational days (`2022-04-01` to `2022-07-10`)  
**Data Integrity:** Analyzed on the final clean dataset (`dataset/cleaned/sales_product_master.csv`) with zero modifications.  

---

## 1. Dataset Overview

The dataset reflects customer grocery ordering behavior across four major Indian metropolitan regions on Flipkart Supermart.

- **Total Sales Transactions:** **46,706,387 rows**
- **Date Span:** **April 1, 2022 to July 10, 2022** (81 recorded operational dates, 101 calendar days)
- **Fulfillment Cities (4):** Bengaluru, Delhi, HR-NCR (Haryana - National Capital Region), and Mumbai
- **Active Products Sold:** **17,304 unique SKUs**
- **Product Hierarchy:**
  - **L0 Categories (Top Level):** 21 categories (e.g., Dry Fruits, Masala & Oil, Dairy & Breakfast, Atta, Rice & Dal, Vegetables & Fruits)
  - **L1 Categories (Sub-level):** 199 sub-categories (e.g., Cooking Oil, Fresh Milk, Fresh Vegetables, Atta)
  - **L2 Categories (Micro-level):** 393 micro-categories

### Key Columns & Business Definitions
- `date_`: Date of transaction order fulfillment.
- `city_name`: Customer delivery metropolitan hub.
- `order_id`: Transactional line-item identifier.
- `procured_quantity`: Physical item count purchased (units).
- `unit_selling_price`: Net consumer selling price per unit in Indian Rupees (₹).
- `total_discount_amount`: Promotional coupon or voucher value deducted.
- `total_weighted_landing_price`: Unit procurement/wholesale inventory landing cost.
- `price_fill_method`: Audit tracking flag documenting whether the landing price is original or deterministically recovered from product-city history.
- `product_id` & `product_name`: Unique SKU number and brand title.
- `l0_category`, `l1_category`, `l2_category`: Standardized 3-tier retail product taxonomy.

---

## 2. Sales & Demand Analysis

Flipkart Supermart processed massive physical volumes over the 81 active operational days:

| Metric | Total Value | Daily Average |
|---|---|---|
| **Total Physical Units Sold** | **60,176,096 units** | **742,915 units / day** |
| **Gross Merchandise Value (GMV)** | **₹4,725,948,522.00 (₹472.59 Cr)** | **₹58,345,043.48 / day (~₹5.83 Cr/day)** |
| **Total Transactions Processed** | **46,706,387 rows** | **576,622 orders / day** |
| **Average Quantity per Line Item** | **1.29 units** | Median: 1.0 unit (Max: 50 units) |
| **Average Revenue per Line Item** | **₹101.18** | Median: ₹50.00 |

### Daily Demand and Revenue Trend
Over the 3.5-month span, daily demand volume steadily expanded from ~650,000 units/day in early April to over 850,000 units/day in early July (+30.7% daily velocity growth).

![Daily Demand and Revenue Trend](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/daily_demand_revenue_trend.png)

---

## 3. City Analysis

Demand is heavily skewed toward North Indian urban clusters (Delhi and HR-NCR).

| City | Total Transactions | Total Units Sold | Volume Share (%) | Gross Revenue (₹) | GMV Share (%) | Active SKUs | Avg Daily Units | Avg Daily GMV (₹) |
|---|---|---|---|---|---|---|---|---|
| **Delhi** | 21,449,858 | 28,075,593 | **46.66%** | ₹2,288,798,124 | **48.43%** | 11,990 | 346,612 | ₹28,256,767 |
| **HR-NCR** | 11,866,528 | 15,339,245 | **25.49%** | ₹1,139,562,783 | **24.11%** | 12,787 | 189,373 | ₹14,068,676 |
| **Bengaluru** | 9,511,508 | 11,747,370 | **19.52%** | ₹865,422,917 | **18.31%** | 10,491 | 145,029 | ₹10,684,234 |
| **Mumbai** | 3,878,493 | 5,013,888 | **8.33%** | ₹432,164,698 | **9.14%** | 11,037 | 61,900 | ₹5,335,367 |

![City Sales Comparison](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/city_sales_comparison.png)

### Key City Insights:
1. **Delhi is the core anchor:** Generates nearly **half of all revenue (48.43%)** and **volume (46.66%)**.
2. **Delhi-NCR Dominance:** Combining Delhi and HR-NCR accounts for **72.54% of total GMV (₹3,428.36 Cr)**. Supply chain, warehouse capacity, and fulfillment nodes must prioritize the NCR hub.
3. **Mumbai has high catalog variety but low volume:** Mumbai carries 11,037 active products (more than Bengaluru's 10,491), yet drives only **9.14% of GMV**, reflecting lower order density and smaller basket velocity per SKU.

---

## 4. Product Analysis & Demand Concentration

### Top 10 Products by Physical Volume (Units Sold)
Daily dairy and fresh kitchen produce dominate physical grocery volume:

| Rank | SKU ID | Product Name | Category | Units Sold | Total Revenue (₹) |
|---|---|---|---|---|---|
| 1 | `19512` | **Amul Taaza Toned Fresh Milk** | Dairy & Breakfast | **1,261,153** | ₹31,410,529 |
| 2 | `391306` | **Onion** | Vegetables & Fruits | **1,171,389** | ₹27,511,576 |
| 3 | `12872` | **Amul Gold Full Cream Fresh Milk** | Dairy & Breakfast | **897,112** | ₹26,829,751 |
| 4 | `3881` | **Hybrid Tomato** | Vegetables & Fruits | **766,785** | ₹19,120,688 |
| 5 | `445675` | **Desi Tomato** | Vegetables & Fruits | **719,921** | ₹18,401,403 |
| 6 | `423735` | **Green Chilli** | Vegetables & Fruits | **521,772** | ₹5,821,489 |
| 7 | `3889` | **Coriander Bunch** | Vegetables & Fruits | **509,505** | ₹4,579,904 |
| 8 | `333785` | **Potato (Chipsona)** | Vegetables & Fruits | **483,844** | ₹12,728,900 |
| 9 | `10088` | **Cucumber** | Vegetables & Fruits | **461,428** | ₹8,149,279 |
| 10 | `3898` | **Lady Finger (Bhindi)** | Vegetables & Fruits | **441,270** | ₹5,981,211 |

### Top 10 Products by Revenue (GMV)
Cooking oils, packaged flours (atta), and branded dairy drive total gross revenue:

| Rank | SKU ID | Product Name | Category | Total Revenue (₹) | Units Sold | Avg Price |
|---|---|---|---|---|---|---|
| 1 | `52` | **Fortune Soya Health Refined Soyabean Oil** | Dry Fruits, Masala & Oil | **₹44,814,504** | 250,055 | ₹179.22 |
| 2 | `333324` | **Aashirvaad Shudh Chakki Atta (10 kg)** | Atta, Rice & Dal | **₹40,646,976** | 110,221 | ₹368.78 |
| 3 | `15907` | **Fortune Kachi Ghani Pure Mustard Oil** | Dry Fruits, Masala & Oil | **₹36,007,725** | 194,562 | ₹185.07 |
| 4 | `19512` | **Amul Taaza Toned Fresh Milk** | Dairy & Breakfast | **₹31,410,529** | 1,261,153 | ₹24.91 |
| 5 | `388639` | **Chakki Atta (10 kg)** | Atta, Rice & Dal | **₹30,364,023** | 97,533 | ₹311.32 |
| 6 | `391306` | **Onion** | Vegetables & Fruits | **₹27,511,576** | 1,171,389 | ₹23.49 |
| 7 | `12872` | **Amul Gold Full Cream Fresh Milk** | Dairy & Breakfast | **₹26,829,751** | 897,112 | ₹29.91 |
| 8 | `383480` | **Maggi Masala Noodles (Pack of 12)** | Instant & Frozen Food | **₹26,704,570** | 175,127 | ₹152.49 |
| 9 | `160` | **Amul Salted Butter** | Dairy & Breakfast | **₹24,163,756** | 97,703 | ₹247.32 |
| 10 | `352443` | **Tender Coconut** | Vegetables & Fruits | **₹22,922,428** | 396,320 | ₹57.84 |

### Demand Concentration (Pareto ABC Analysis)
An extreme Pareto principle governs retail grocery demand:
- **Top 10% of products (1,731 SKUs):** Drive **73.6% of total revenue**.
- **Top 20% of products (3,461 SKUs):** Drive **82.9% of total revenue**.
- **The "Vital Few" Threshold:** Exactly **231 products (1.33% of catalog)** generate **80.0% of all grocery GMV**.

![Pareto Demand Concentration](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/pareto_demand_concentration.png)

---

## 5. Category Analysis

Grocery purchases are concentrated in four core staple categories that fulfill daily kitchen necessities.

| Category (L0) | GMV (₹) | GMV Share (%) | Physical Units | Volume Share (%) | SKU Count | Avg Price |
|---|---|---|---|---|---|---|
| **Dry Fruits, Masala & Oil** | ₹815,641,197 | **17.26%** | 5,572,465 | 9.26% | 1,030 | ₹146.37 |
| **Dairy & Breakfast** | ₹547,623,366 | **11.59%** | 10,397,163 | **17.28%** | 650 | ₹52.67 |
| **Atta, Rice & Dal** | ₹540,824,597 | **11.44%** | 4,148,284 | 6.89% | 621 | ₹130.37 |
| **Vegetables & Fruits** | ₹491,973,610 | **10.41%** | 14,758,468 | **24.53%** | 422 | ₹33.34 |
| **Personal Care** | ₹320,269,061 | 6.78% | 1,890,595 | 3.14% | 1,761 | ₹169.40 |
| **Cleaning Essentials** | ₹308,661,433 | 6.53% | 1,980,811 | 3.29% | 753 | ₹155.83 |
| **Cold Drinks & Juices** | ₹255,625,764 | 5.41% | 3,999,072 | 6.65% | 766 | ₹63.92 |
| **Tea, Coffee & Drinks** | ₹205,651,092 | 4.35% | 2,351,221 | 3.91% | 975 | ₹87.47 |
| **Munchies** | ₹195,479,259 | 4.14% | 4,364,858 | 7.25% | 1,180 | ₹44.78 |
| **Instant & Frozen Food** | ₹194,664,391 | 4.12% | 2,092,250 | 3.48% | 880 | ₹93.04 |
| *Top 10 Category Subtotal* | *₹3,876,413,770* | *82.02%* | *51,555,187* | *85.67%* | *9,038* | — |

![Top Categories by Revenue](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/top_categories_l0.png)

### Category Hierarchy Insights (L1 Subcategories):
1. **Cooking Oil (L1):** Largest individual revenue subcategory (**₹35.40 Cr, 7.49% GMV**). Driven by edible oil brands (Fortune, Saffola).
2. **Fresh Vegetables (L1):** Highest transactional frequency (**7,421,309 transaction rows, 9.63M units, ₹23.27 Cr**).
3. **Fresh Milk (L1):** Second highest volume driver (**4.66M units, ₹14.13 Cr**). High turnover, short shelf-life.
4. **Atta (Packaged Flour) (L1):** Third highest GMV subcategory (**₹17.75 Cr, 3.76% GMV**). High bulk weight per item.

---

## 6. Time Analysis & Seasonality

### Monthly Progression (Steady Velocity Growth)

| Month | Operational Days | Total Units Sold | Total Gross Revenue (₹) | Daily Quantity Velocity | Daily Revenue Velocity (₹) |
|---|---|---|---|---|---|
| **April 2022** | 30 days | 20,286,103 | ₹1,542,732,389 | 676,203 units / day | ₹51,424,413 / day |
| **May 2022** | 21 days | 16,024,552 | ₹1,216,468,062 | 763,074 units / day | ₹57,927,051 / day |
| **June 2022** | 20 days | 15,373,127 | ₹1,241,662,776 | 768,656 units / day | ₹62,083,139 / day |
| **July 2022** | 10 days | 8,492,314 | ₹725,085,295 | 849,231 units / day | ₹72,508,530 / day |

*Daily sales run-rate expanded by **+25.6% in units** and **+41.0% in GMV** from April to early July, indicating platform adoption and grocery order consolidation.*

### Day of the Week Seasonality (The Weekend Surge)

| Day of Week | Recorded Days | Average Daily Demand (Units) | Average Daily Revenue (₹) | Lift vs Monday |
|---|---|---|---|---|
| **Monday** | 11 | 691,576 | ₹53,658,016 | Baseline (0.0%) |
| **Tuesday** | 10 | 704,401 | ₹54,935,156 | +1.9% |
| **Wednesday** | 11 | 707,938 | ₹55,462,944 | +2.4% |
| **Thursday** | 11 | 717,263 | ₹55,639,262 | +3.7% |
| **Friday** | 13 | 722,765 | ₹56,350,967 | +4.5% |
| **Saturday** | 13 | **788,757** | **₹62,157,690** | **+14.1%** |
| **Sunday** | 12 | **849,814** | **₹68,635,166** | **+22.9%** |

![Day of Week Demand Pattern](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/day_of_week_demand.png)

### Key Temporal Patterns:
- **Sunday is the undisputed peak:** Averages **849,814 units/day**, outperforming Monday by nearly **160,000 units per day (+22.9%)**.
- **Weekend Effect:** Combined Saturday and Sunday demand averages **819,285 units/day**, compared to **708,788 units/day on weekdays (+15.6% weekend surge)**.

---

## 7. Price & Discount Analysis

### Selling Price Distribution
- **Minimum:** ₹0.00 (promotional giveaways)
- **25th Percentile ($P_{25}$):** **₹27.00**
- **Median ($P_{50}$):** **₹50.00**
- **75th Percentile ($P_{75}$):** **₹102.00**
- **90th Percentile ($P_{90}$):** **₹195.00**
- **99th Percentile ($P_{99}$):** **₹514.00**
- **Maximum:** **₹10,999.00** (Product `477200`)
- **Mean:** **₹87.17**

*Over 75% of items sell for ₹102 or less, reflecting affordable, everyday grocery consumption.*

### Discount Dynamics
- **Total Promotional Discounts Given:** **₹29,431,020.34 (₹2.94 Cr)** across 81 days.
- **Transactions with Zero Discount:** **45,629,057 rows (97.7%)**.
- **Transactions with Discounts:** **1,077,330 rows (2.3%)**.
- **When Discount is Present:**
  - Median Discount: **₹12.00**
  - Average Discount: **₹27.32**
  - Maximum Discount: **₹1,500.00**
- **Insight:** Flipkart Supermart relies primarily on competitive shelf prices rather than universal promotional coupons. Discounts are targeted promotions applied to only 2.3% of transaction lines.

---

## 8. Data Quality Observations (Not Cleaning Tasks)

The following observations reflect real operational conditions and should be understood by downstream models:

1. **Unmatched Product IDs (1,496 SKUs / 532,122 rows / 1.14%):**
   - Valid integer IDs ranging from 57 to 488,730 that were simply absent from the master catalog export.
   - Generate ₹5.78 Cr revenue and 629k units. They are real sales records.
   - Their attributes are properly marked `NOT_AVAILABLE / NaN`.
2. **Unresolved Landing Prices (41,871 rows across 14 SKUs):**
   - 14 products never had a cost record in the system.
   - Kept as `NaN` to preserve integrity (zero synthetic cost guessing).
3. **Zero Procured Quantity (184,411 rows / 0.39%):**
   - Represents cancelled items, basket line modifications, or customer drop-offs recorded at checkout.
   - Useful for order modification / cancellation analysis.
4. **Zero Unit Selling Price (125,349 rows / 0.27%):**
   - Free marketing samples, complementary onboarding gifts, or promotional zero-priced items.
   - Legitimate physical volume that must be forecasted for warehouse inventory even if revenue is zero.
5. **Discount Exceeding Line Revenue (231 rows):**
   - Occurs when fixed-value promotional cart vouchers (e.g. ₹50 off) apply to a small item (e.g. ₹30 biscuit). Real e-commerce voucher edge case.

---

## 9. Actionable Business Insights

1. **North India Fulfillment Hub:** Delhi and HR-NCR drive **72.5% of total GMV**. Warehouse capacity, delivery fleet sizing, and vendor logistics must be optimized primarily for the NCR cluster.
2. **Weekend Capacity Planning:** Delivery fleet and warehouse picker staffing must be scaled up by **15% to 23% on Saturdays and Sundays** to handle the systematic weekend demand surge.
3. **Oil and Ghee Are Margin Engines:** Cooking Oil and Ghee account for over **10.3% of total platform GMV** with high average order value (AOV). Supplier contract terms and volume rebates in edible oils directly impact gross margins.
4. **Produce and Dairy Are Retention Hooks:** Fresh Vegetables and Milk account for **41.8% of all physical items handled**. While margins per unit are lower, daily fresh availability is the primary driver of customer retention and purchase frequency.
5. **Pareto Inventory Protection (ABC Classification):** Exactly **231 products drive 80% of revenue**. These 231 "Class A" SKUs should receive top-tier safety stock, guaranteed supplier delivery SLAs, and multi-supplier sourcing to prevent catastrophic stockouts.
6. **Mumbai Catalog Rationalization:** Mumbai carries 11,037 SKUs but generates only 9.1% of revenue. Slow-moving tail SKUs in Mumbai can be trimmed to reduce storage overhead.
7. **Promotion-Independent Core Business:** 97.7% of lines sell at full price without coupons. Platform revenue is structurally resilient and does not depend on deep promotional discounting.
8. **Bulk Packaged Staples Drive Basket Value:** 10 kg Atta packs (Aashirvaad and Chakki Atta) generate over ₹7.1 Cr GMV across just two SKUs. Bulk storage and heavy transport handling are required.
9. **Single-Item Cart Skew:** Median purchase quantity is 1 unit. Rapid order-picking layout should group high-frequency items (milk, onion, tomato, bread) near warehouse dispatch bays.
10. **Consistent Multi-City Product Footprint:** Top products like Amul Taaza Milk, Hybrid Tomato, and Onions sell consistently across all four cities, confirming universal demand patterns across metropolitan demographics.

---

## 10. Forecasting-Relevant Insights

Downstream machine learning models and inventory algorithms should incorporate these structural patterns:

1. **Day-of-Week Seasonality (`day_of_week`, `is_weekend`):** Demand strongly peaks on weekends. Calendar features are non-negotiable for accurate short-term horizons.
2. **Month-Start Grocery Restock:** Peak demand occurs in the first 7 days of each calendar month as households replenish staple pantries (oil, atta, rice, detergent).
3. **Severe Intermittency in Tail SKUs:** While the top 231 SKUs have continuous daily sales, over 8,000 tail products have intermittent sales (zero-demand on 70%+ of days). Forecasting models must handle zero-inflated demand.
4. **High-Volume Dairy Dynamics:** Fresh milk (SKU `19512`) sells >15,000 units/day in Delhi alone with low volatility but extreme spoilage risk. Requires short-horizon (1-day to 3-day) autoregressive lag features (`lag_1`, `lag_7`).
5. **Fresh Produce Volatility:** Produce (tomatoes, onions) exhibits seasonal price and volume swings. Lagged rolling demand (`rolling_mean_7`, `rolling_mean_14`) smooths transient price spikes.
6. **Zero-Price Volume Forecasting:** The 125k free promotional sample units must be forecasted as physical warehouse demand even though revenue is ₹0.
