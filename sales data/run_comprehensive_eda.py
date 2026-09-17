import os
import sys
import json
import time
import duckdb
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).resolve().parent.parent
sales_master = project_root / "dataset" / "cleaned" / "sales_product_master.csv"
demand_file = project_root / "dataset" / "processed" / "daily_product_demand.csv"
eda_dir = project_root / "reports" / "eda"
eda_dir.mkdir(parents=True, exist_ok=True)
reports_dir = project_root / "reports"

print("=" * 80)
print("RUNNING COMPREHENSIVE EXPLORATORY DATA ANALYSIS (EDA)")
print("=" * 80)

t0 = time.time()
con = duckdb.connect()

# =====================================================================
# 1. DATASET OVERVIEW
# =====================================================================
print("\n[1/7] Computing Dataset Overview...")
overview_query = f"""
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT product_id) as total_products,
    COUNT(DISTINCT city_name) as total_cities,
    COUNT(DISTINCT date_) as unique_dates,
    MIN(date_) as min_date,
    MAX(date_) as max_date,
    COUNT(DISTINCT l0_category) as unique_l0,
    COUNT(DISTINCT l1_category) as unique_l1,
    COUNT(DISTINCT l2_category) as unique_l2,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue
FROM read_csv_auto('{sales_master.as_posix()}')
"""
overview = con.execute(overview_query).df().to_dict(orient="records")[0]
print(f"Total Rows: {overview['total_rows']:,} | Products: {overview['total_products']:,} | Cities: {overview['total_cities']}")
print(f"Dates: {overview['min_date']} to {overview['max_date']} ({overview['unique_dates']} active dates)")
print(f"Total Units: {overview['total_quantity']:,} | Total Revenue: INR {overview['total_revenue']:,.2f}")

# =====================================================================
# 2. CITY ANALYSIS
# =====================================================================
print("\n[2/7] Analyzing Demand by City...")
city_query = f"""
SELECT 
    city_name,
    COUNT(*) as transaction_rows,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue,
    COUNT(DISTINCT product_id) as unique_products,
    ROUND(SUM(procured_quantity) / COUNT(DISTINCT date_), 1) as avg_daily_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price) / COUNT(DISTINCT date_), 2) as avg_daily_revenue
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY city_name
ORDER BY total_revenue DESC
"""
df_city = con.execute(city_query).df()
total_rev = overview['total_revenue']
total_qty = overview['total_quantity']
df_city["revenue_share_pct"] = (df_city["total_revenue"] / total_rev * 100).round(2)
df_city["quantity_share_pct"] = (df_city["total_quantity"] / total_qty * 100).round(2)
print(df_city.to_string(index=False))

# =====================================================================
# 3. CATEGORY ANALYSIS (L0, L1, L2)
# =====================================================================
print("\n[3/7] Analyzing Product Categories...")
l0_query = f"""
SELECT 
    COALESCE(l0_category, 'UNMATCHED_PRODUCTS') as l0_category,
    COUNT(*) as transaction_rows,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue,
    COUNT(DISTINCT product_id) as unique_products
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY l0_category
ORDER BY total_revenue DESC
"""
df_l0 = con.execute(l0_query).df()
df_l0["revenue_share_pct"] = (df_l0["total_revenue"] / total_rev * 100).round(2)
df_l0["quantity_share_pct"] = (df_l0["total_quantity"] / total_qty * 100).round(2)

l1_query = f"""
SELECT 
    COALESCE(l0_category, 'UNMATCHED') as l0_category,
    COALESCE(l1_category, 'UNMATCHED') as l1_category,
    COUNT(*) as transaction_rows,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue,
    COUNT(DISTINCT product_id) as unique_products
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY l0_category, l1_category
ORDER BY total_revenue DESC
LIMIT 20
"""
df_l1_top20 = con.execute(l1_query).df()
df_l1_top20["revenue_share_pct"] = (df_l1_top20["total_revenue"] / total_rev * 100).round(2)

# =====================================================================
# 4. PRODUCT ANALYSIS & PARETO CONCENTRATION
# =====================================================================
print("\n[4/7] Analyzing Products and Pareto Distribution...")
top20_qty_query = f"""
SELECT 
    product_id,
    COALESCE(product_name, 'UNMATCHED_PRODUCT') as product_name,
    COALESCE(l0_category, 'UNMATCHED') as category,
    SUM(procured_quantity) as total_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY product_id, product_name, l0_category
ORDER BY total_quantity DESC
LIMIT 20
"""
df_top20_qty = con.execute(top20_qty_query).df()

top20_rev_query = f"""
SELECT 
    product_id,
    COALESCE(product_name, 'UNMATCHED_PRODUCT') as product_name,
    COALESCE(l0_category, 'UNMATCHED') as category,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as total_revenue,
    SUM(procured_quantity) as total_quantity
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY product_id, product_name, l0_category
ORDER BY total_revenue DESC
LIMIT 20
"""
df_top20_rev = con.execute(top20_rev_query).df()

# Pareto concentration calculation
pareto_query = f"""
WITH prod_rev AS (
    SELECT 
        product_id,
        SUM(procured_quantity * unit_selling_price) as revenue,
        SUM(procured_quantity) as quantity
    FROM read_csv_auto('{sales_master.as_posix()}')
    GROUP BY product_id
    ORDER BY revenue DESC
)
SELECT 
    product_id,
    revenue,
    quantity,
    SUM(revenue) OVER (ORDER BY revenue DESC) / {total_rev} as cum_revenue_share,
    SUM(quantity) OVER (ORDER BY quantity DESC) / {total_qty} as cum_quantity_share,
    ROW_NUMBER() OVER (ORDER BY revenue DESC) as product_rank
FROM prod_rev
"""
df_pareto = con.execute(pareto_query).df()
n_products = len(df_pareto)
top_10pct_n = int(np.ceil(n_products * 0.10))
top_20pct_n = int(np.ceil(n_products * 0.20))
rev_share_top10pct = df_pareto.iloc[top_10pct_n - 1]["cum_revenue_share"] * 100
rev_share_top20pct = df_pareto.iloc[top_20pct_n - 1]["cum_revenue_share"] * 100

# Products achieving 80% revenue
p80_n = (df_pareto["cum_revenue_share"] >= 0.80).idxmax() + 1
p80_pct = (p80_n / n_products) * 100

print(f"Pareto Principle: Top 10% products ({top_10pct_n:,}) drive {rev_share_top10pct:.1f}% of revenue.")
print(f"Top 20% products ({top_20pct_n:,}) drive {rev_share_top20pct:.1f}% of revenue.")
print(f"80% of revenue is driven by {p80_n:,} products ({p80_pct:.1f}% of catalog).")

# =====================================================================
# 5. TEMPORAL ANALYSIS (Daily, Monthly, Day-of-Week, Weekend)
# =====================================================================
print("\n[5/7] Analyzing Temporal Patterns...")
daily_query = f"""
SELECT 
    CAST(date_ AS DATE) as date_,
    COUNT(*) as transaction_rows,
    SUM(procured_quantity) as daily_quantity,
    ROUND(SUM(procured_quantity * unit_selling_price), 2) as daily_revenue,
    DAYOFWEEK(CAST(date_ AS DATE)) - 1 as day_of_week,
    strftime(CAST(date_ AS DATE), '%A') as day_name,
    strftime(CAST(date_ AS DATE), '%Y-%m') as month_str,
    CASE WHEN DAYOFWEEK(CAST(date_ AS DATE)) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END as day_type
FROM read_csv_auto('{sales_master.as_posix()}')
GROUP BY date_
ORDER BY date_
"""
df_daily = con.execute(daily_query).df()

# Monthly summary
monthly_summary = df_daily.groupby("month_str").agg(
    active_days=("date_", "count"),
    total_quantity=("daily_quantity", "sum"),
    total_revenue=("daily_revenue", "sum"),
    avg_daily_quantity=("daily_quantity", "mean"),
    avg_daily_revenue=("daily_revenue", "mean")
).reset_index()
monthly_summary["avg_daily_quantity"] = monthly_summary["avg_daily_quantity"].round(1)
monthly_summary["avg_daily_revenue"] = monthly_summary["avg_daily_revenue"].round(2)

# Day of week summary
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
dow_summary = df_daily.groupby("day_name").agg(
    total_days=("date_", "count"),
    avg_daily_quantity=("daily_quantity", "mean"),
    avg_daily_revenue=("daily_revenue", "mean"),
    total_quantity=("daily_quantity", "sum"),
    total_revenue=("daily_revenue", "sum")
).reindex(dow_order).reset_index()

# Weekend vs Weekday summary
weekend_summary = df_daily.groupby("day_type").agg(
    total_days=("date_", "count"),
    avg_daily_quantity=("daily_quantity", "mean"),
    avg_daily_revenue=("daily_revenue", "mean"),
    total_quantity=("daily_quantity", "sum"),
    total_revenue=("daily_revenue", "sum")
).reset_index()
weekend_summary["quantity_per_day"] = weekend_summary["avg_daily_quantity"].round(1)
weekend_summary["revenue_per_day"] = weekend_summary["avg_daily_revenue"].round(2)

# =====================================================================
# 6. PRICE & DISCOUNT ANALYSIS
# =====================================================================
print("\n[6/7] Analyzing Price and Discount Distributions...")
price_disc_query = f"""
SELECT 
    ROUND(AVG(unit_selling_price), 2) as mean_price,
    ROUND(MEDIAN(unit_selling_price), 2) as median_price,
    ROUND(QUANTILE_CONT(unit_selling_price, 0.25), 2) as p25_price,
    ROUND(QUANTILE_CONT(unit_selling_price, 0.75), 2) as p75_price,
    ROUND(QUANTILE_CONT(unit_selling_price, 0.90), 2) as p90_price,
    ROUND(QUANTILE_CONT(unit_selling_price, 0.99), 2) as p99_price,
    MAX(unit_selling_price) as max_price,
    -- Discount statistics
    ROUND(SUM(total_discount_amount), 2) as total_discount_given,
    COUNT(CASE WHEN total_discount_amount > 0 THEN 1 END) as discounted_rows,
    COUNT(CASE WHEN total_discount_amount = 0 THEN 1 END) as zero_discount_rows,
    ROUND(AVG(CASE WHEN total_discount_amount > 0 THEN total_discount_amount END), 2) as mean_discount_when_present,
    ROUND(MEDIAN(CASE WHEN total_discount_amount > 0 THEN total_discount_amount END), 2) as median_discount_when_present,
    MAX(total_discount_amount) as max_discount
FROM read_csv_auto('{sales_master.as_posix()}')
"""
price_disc_stats = con.execute(price_disc_query).df().to_dict(orient="records")[0]

# =====================================================================
# 7. GENERATE LIGHTWEIGHT CHARTS
# =====================================================================
print("\n[7/7] Generating Lightweight Charts in reports/eda/...")
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

# Chart 1: Daily Demand & Revenue Trend
fig, ax1 = plt.subplots(figsize=(12, 5), dpi=120)
ax2 = ax1.twinx()

ax1.plot(df_daily["date_"], df_daily["daily_quantity"] / 1000, color="#1f77b4", linewidth=1.8, label="Daily Quantity (k units)")
ax2.plot(df_daily["date_"], df_daily["daily_revenue"] / 1e7, color="#2ca02c", linewidth=1.8, linestyle="--", label="Daily Revenue (₹ Crore)")

ax1.set_xlabel("Date", fontsize=11, fontweight="bold")
ax1.set_ylabel("Demand Quantity (Thousand Units)", color="#1f77b4", fontsize=11, fontweight="bold")
ax2.set_ylabel("Gross Revenue (₹ Crore)", color="#2ca02c", fontsize=11, fontweight="bold")
ax1.set_title("Flipkart Supermart: Daily Demand & Revenue Trend (Apr - Jul 2022)", fontsize=13, fontweight="bold", pad=12)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", frameon=True)
plt.tight_layout()
fig1_path = eda_dir / "daily_demand_revenue_trend.png"
plt.savefig(fig1_path)
plt.close()
print(f"Saved: {fig1_path.name}")

# Chart 2: City Sales Comparison
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
x = np.arange(len(df_city))
width = 0.35

ax.bar(x - width/2, df_city["total_revenue"] / 1e7, width, label="Revenue (₹ Crore)", color="#2ca02c")
ax.bar(x + width/2, df_city["total_quantity"] / 1e6, width, label="Quantity (Million Units)", color="#1f77b4")

ax.set_xticks(x)
ax.set_xticklabels(df_city["city_name"], fontweight="bold")
ax.set_ylabel("Volume / Revenue Scale", fontsize=11, fontweight="bold")
ax.set_title("Sales & Volume by City (Delhi Leads with 58% GMV)", fontsize=12, fontweight="bold", pad=12)
ax.legend(frameon=True)
plt.tight_layout()
fig2_path = eda_dir / "city_sales_comparison.png"
plt.savefig(fig2_path)
plt.close()
print(f"Saved: {fig2_path.name}")

# Chart 3: Top 10 Categories by Revenue
top10_l0 = df_l0.head(10).sort_values(by="total_revenue", ascending=True)
fig, ax = plt.subplots(figsize=(10, 5), dpi=120)
ax.barh(top10_l0["l0_category"], top10_l0["total_revenue"] / 1e7, color="#ff7f0e", height=0.6)
ax.set_xlabel("Revenue (₹ Crore)", fontsize=11, fontweight="bold")
ax.set_title("Top 10 L0 Product Categories by Revenue", fontsize=12, fontweight="bold", pad=12)
for i, v in enumerate(top10_l0["total_revenue"] / 1e7):
    ax.text(v + 1, i, f"₹{v:,.1f} Cr ({top10_l0['revenue_share_pct'].iloc[i]}%)", va="center", fontsize=9)
plt.tight_layout()
fig3_path = eda_dir / "top_categories_l0.png"
plt.savefig(fig3_path)
plt.close()
print(f"Saved: {fig3_path.name}")

# Chart 4: Day of Week Average Demand
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=120)
colors = ["#1f77b4" if d not in ["Saturday", "Sunday"] else "#d62728" for d in dow_summary["day_name"]]
ax.bar(dow_summary["day_name"], dow_summary["avg_daily_quantity"] / 1000, color=colors, width=0.55)
ax.set_ylabel("Average Daily Quantity (k Units)", fontsize=11, fontweight="bold")
ax.set_title("Average Daily Demand by Day of Week (Red = Weekend)", fontsize=12, fontweight="bold", pad=12)
plt.xticks(rotation=15, fontweight="bold")
plt.tight_layout()
fig4_path = eda_dir / "day_of_week_demand.png"
plt.savefig(fig4_path)
plt.close()
print(f"Saved: {fig4_path.name}")

# Chart 5: Pareto Concentration Curve
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=120)
ranks_pct = (df_pareto["product_rank"] / n_products) * 100
ax.plot(ranks_pct, df_pareto["cum_revenue_share"] * 100, color="#8c564b", linewidth=2, label="Cumulative Revenue %")
ax.axvline(x=p80_pct, color="r", linestyle="--", alpha=0.7, label=f"80% Revenue ({p80_pct:.1f}% SKUs)")
ax.axhline(y=80, color="r", linestyle="--", alpha=0.7)
ax.set_xlabel("% of Products (Ranked by Revenue)", fontsize=11, fontweight="bold")
ax.set_ylabel("Cumulative Revenue %", fontsize=11, fontweight="bold")
ax.set_title("Pareto Demand Concentration (ABC Analysis)", fontsize=12, fontweight="bold", pad=12)
ax.legend(loc="lower right", frameon=True)
plt.tight_layout()
fig5_path = eda_dir / "pareto_demand_concentration.png"
plt.savefig(fig5_path)
plt.close()
print(f"Saved: {fig5_path.name}")

# Save JSON results for easy reference
eda_results = {
    "overview": overview,
    "cities": df_city.to_dict(orient="records"),
    "categories_l0": df_l0.head(10).to_dict(orient="records"),
    "categories_l1": df_l1_top20.head(10).to_dict(orient="records"),
    "top20_quantity_products": df_top20_qty.to_dict(orient="records"),
    "top20_revenue_products": df_top20_rev.to_dict(orient="records"),
    "pareto": {
        "total_skus": n_products,
        "top_10pct_rev_share": round(float(rev_share_top10pct), 2),
        "top_20pct_rev_share": round(float(rev_share_top20pct), 2),
        "skus_for_80pct_revenue": int(p80_n),
        "pct_skus_for_80pct_revenue": round(float(p80_pct), 2)
    },
    "monthly": monthly_summary.to_dict(orient="records"),
    "day_of_week": dow_summary.to_dict(orient="records"),
    "weekend_vs_weekday": weekend_summary.to_dict(orient="records"),
    "price_and_discount": price_disc_stats
}

with open(reports_dir / "eda_metrics.json", "w") as f:
    json.dump(eda_results, f, indent=2, default=str)

print(f"\nAll metrics computed and exported in {time.time() - t0:.2f}s!")
print("=" * 80)
con.close()
