# Exploratory Data Analysis (EDA) — Executive Summary
**Project:** Demand-Decision-Intelligence  
**Dataset:** Flipkart Supermart Indian Grocery Transactions (`dataset/cleaned/sales_product_master.csv`)  
**Scope:** 46,706,387 transactions | 81 active days (`2022-04-01` to `2022-07-10`)  

---

## 1. High-Level Summary Table

| Business Dimension | Metric / Metric Value | Key Takeaway |
|---|---|---|
| **Total Scale** | **46,706,387 orders \| 60,176,096 units** | High-velocity Indian grocery e-commerce operation |
| **Gross Revenue (GMV)** | **₹4,725,948,522.00 (₹472.59 Crore)** | Averaging **₹5.83 Crore / day** across 4 cities |
| **Fulfillment Geography** | **Delhi, HR-NCR, Bengaluru, Mumbai** | Delhi-NCR drives **72.5% of total GMV** |
| **Active Catalog** | **17,304 unique SKUs** | Top 231 SKUs (1.33%) generate **80% of revenue** |
| **Top Category (Revenue)** | **Dry Fruits, Masala & Oil (₹81.56 Cr / 17.3%)** | Edible oils (Fortune, Saffola) drive high basket value |
| **Top Category (Volume)** | **Vegetables & Fruits (14.76M units / 24.5%)** | Produce + Milk drive **41.8% of all physical units** |
| **Temporal Seasonality** | **Sunday: 849k units/day (+22.9% vs Monday)** | Massive weekend shopping surge (Saturday & Sunday) |
| **Price Point** | **Median Price: ₹50.00 \| Mean: ₹87.17** | 75% of purchases are under ₹102 |
| **Promotional Profile** | **97.7% lines sell at ₹0 discount** | Structurally resilient, shelf-price driven retail demand |

---

## 2. Five Core Visualizations Generated

All lightweight charts are saved and viewable in [`reports/eda/`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/):
1. [`daily_demand_revenue_trend.png`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/daily_demand_revenue_trend.png): Daily volume growth from 650k units/day in April to 850k units/day in July (+30.7%).
2. [`city_sales_comparison.png`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/city_sales_comparison.png): Visualizing Delhi's 48.4% GMV share and NCR dominance.
3. [`top_categories_l0.png`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/top_categories_l0.png): Revenue distribution across top grocery categories.
4. [`day_of_week_demand.png`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/day_of_week_demand.png): Clear Monday-to-Sunday demand progression highlighting the weekend surge.
5. [`pareto_demand_concentration.png`](file:///c:/Users/qaziu/Downloads/Demand-Decision-Intelligence-main/reports/eda/pareto_demand_concentration.png): The classic 80/20 ABC demand concentration curve.

---

## 3. Geographic Concentration

```
[Total Platform Revenue: ₹472.59 Crore]
   ├── Delhi:      ₹228.88 Cr (48.4%) | 28.08M units (46.7%)
   ├── HR-NCR:     ₹113.96 Cr (24.1%) | 15.34M units (25.5%)
   ├── Bengaluru:   ₹86.54 Cr (18.3%) | 11.75M units (19.5%)
   └── Mumbai:      ₹43.22 Cr  (9.1%) |  5.01M units  (8.3%)
```

- **Delhi-NCR represents 72.5% of total business.** Logistics, vendor hubs, and dark-store inventory allocation should be optimized around Delhi and Gurgaon/Noida fulfillment hubs.

---

## 4. Category Dynamics: Revenue vs Volume Engines

Retail grocery divides cleanly into **High-GMV Basket Builders** and **High-Frequency Traffic Drivers**:

| Category Type | Exemplary Categories | Commercial Role | Operational Priority |
|---|---|---|---|
| **Revenue Engines** | Cooking Oil, Atta, Ghee, Spices | High unit price (₹130 – ₹185), bulk pack sizes, steady velocity | Maximize supplier margin, bulk pallet storage |
| **Volume Drivers** | Fresh Vegetables, Fresh Milk, Bread | Low unit price (₹20 – ₹35), high daily repeat purchases | Rapid turnover, cold-chain, zero stockouts |
| **Impulse / FMCG** | Munchies, Biscuits, Soft Drinks | Medium price (₹40 – ₹65), weekend-skewed spikes | Display marketing, pack bundling |

---

## 5. Top 5 Actionable Takeaways for Forecasting & Supply Chain

1. **Protect Class-A Inventory (231 SKUs):** Just 231 products generate 80% of all platform revenue. These products must have guaranteed safety stock and multi-vendor delivery SLAs.
2. **Staff Up for Weekend Peaks:** Saturday and Sunday experience a **+15.6% overall volume surge** (peaking at +22.9% on Sundays). Fulfillment pickers, packers, and delivery fleets must scale up on weekends.
3. **Capture Month-Start Grocery Restocking:** Indian households restock heavy staples (10kg Atta, 5L Oil, Detergent) during the 1st to 7th of every month. Forecasting models must capture calendar day-of-month effects.
4. **Treat Zero-Price Samples as Physical Volume:** The 125,349 zero-price items represent physical warehouse dispatch demand and truck volume, even if revenue is zero.
5. **Account for Intermittent Tail Demand:** While top products have steady daily sales, tail SKUs experience zero demand on 70%+ of days. Forecasting algorithms must handle zero-inflated, intermittent demand patterns.
