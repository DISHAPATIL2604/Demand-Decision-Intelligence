import json
import duckdb
import numpy as np
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
demand_file = project_root / "dataset" / "processed" / "daily_product_demand.csv"
lp_lookup_file = project_root / "dataset" / "processed" / "landing_price_recovery_lookup.csv"
reports_dir = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)
inventory_dir = project_root / "inventory"
inventory_dir.mkdir(parents=True, exist_ok=True)

print("=" * 75)
print("DEMAND DECISION INTELLIGENCE: INVENTORY DECISION ENGINE (PHASE 9)")
print("=" * 75)

# Standard normal Z-score lookup table for common service levels
Z_SCORES = {
    0.90: 1.282,
    0.95: 1.645,
    0.98: 2.054,
    0.99: 2.326
}

def generate_inventory_decisions(
    lead_time_days: int = 3,
    target_service_level: float = 0.95,
    review_period_days: int = 7,
    sample_size: int = None
):
    """
    Computes Safety Stock, Reorder Point, and Target Inventory for all product-city series.
    
    DATA INTEGRITY COMPLIANCE:
    - Lead time (L) and Service Level (SL) do NOT exist in raw Flipkart data.
      They are strictly marked as NOT_AVAILABLE in the original dataset and provided
      as configurable external business parameters.
    - Demand parameters (mean daily demand, standard deviation) are derived strictly
      from historical actuals in daily_product_demand.csv.
    - Unit landing cost is joined from the deterministic landing price recovery table.
    """
    z_value = Z_SCORES.get(target_service_level, 1.645)
    
    con = duckdb.connect()
    
    print("\nCalculating demand parameters (mean, std) per product-city across recent 30-day window...")
    query = f"""
    WITH recent_demand AS (
        SELECT 
            product_id,
            city_name,
            CAST(date_ AS DATE) as date_,
            daily_quantity
        FROM read_csv_auto('{demand_file.as_posix()}')
        WHERE CAST(date_ AS DATE) >= DATE '2022-06-11' AND CAST(date_ AS DATE) <= DATE '2022-07-10'
    ),
    series_stats AS (
        SELECT 
            product_id,
            city_name,
            AVG(daily_quantity) as avg_daily_demand,
            COALESCE(STDDEV(daily_quantity), 0.0) as std_daily_demand,
            COUNT(*) as active_days_in_window
        FROM recent_demand
        GROUP BY product_id, city_name
    )
    SELECT 
        s.product_id,
        s.city_name,
        ROUND(s.avg_daily_demand, 2) as mean_daily_demand,
        ROUND(s.std_daily_demand, 2) as std_daily_demand,
        s.active_days_in_window,
        lp.recovered_landing_price as unit_cost,
        lp.recovery_tier as cost_data_status
    FROM series_stats s
    LEFT JOIN read_csv_auto('{lp_lookup_file.as_posix()}') lp
        ON s.product_id = lp.product_id AND s.city_name = lp.city_name
    ORDER BY s.avg_daily_demand DESC
    """
    
    df = con.execute(query).df()
    con.close()
    
    if sample_size is not None:
        df = df.head(sample_size).copy()
    
    # Mathematical Inventory Calculations
    # 1. Lead Time Demand = Mean * L
    df["lead_time_days_param"] = lead_time_days
    df["target_service_level_param"] = target_service_level
    df["lead_time_demand"] = df["mean_daily_demand"] * lead_time_days
    
    # 2. Safety Stock = Z * std_d * sqrt(L)
    df["safety_stock"] = np.ceil(z_value * df["std_daily_demand"] * np.sqrt(lead_time_days)).astype(int)
    
    # 3. Reorder Point (ROP) = Lead Time Demand + Safety Stock
    df["reorder_point"] = np.ceil(df["lead_time_demand"] + df["safety_stock"]).astype(int)
    
    # 4. Target Stock Level (Order-up-to level) = Mean * (L + R) + Safety Stock
    df["target_stock_level"] = np.ceil(df["mean_daily_demand"] * (lead_time_days + review_period_days) + df["safety_stock"]).astype(int)
    
    # Tag status of external parameters
    df["lead_time_source"] = "NOT_AVAILABLE_IN_SOURCE (Configured Parameter)"
    df["service_level_source"] = "NOT_AVAILABLE_IN_SOURCE (Configured Parameter)"
    df["cost_data_status"] = df["cost_data_status"].fillna("ORIGINAL_VALID_IN_MASTER")
    
    return df

if __name__ == "__main__":
    df_inv = generate_inventory_decisions(lead_time_days=3, target_service_level=0.95, review_period_days=7)
    
    print(f"Total inventory decision series: {len(df_inv):,}")
    print("\nSample Inventory Decision Policies (Top 10 highest demand series):")
    sample_cols = [
        "product_id", "city_name", "mean_daily_demand", "std_daily_demand",
        "lead_time_days_param", "safety_stock", "reorder_point", "target_stock_level", "cost_data_status"
    ]
    print(df_inv[sample_cols].head(10).to_string(index=False))
    
    # Save top 1000 sample policy for review and API integration
    output_csv = reports_dir / "inventory_decision_sample.csv"
    df_inv.head(1000).to_csv(output_csv, index=False)
    print(f"\nSaved inventory policy sample (1,000 rows) to: {output_csv}")
    
    # Save full inventory summary metadata
    inv_metadata = {
        "engine": "Dynamic Lead-Time Demand + Variance Safety Stock",
        "formulas": {
            "safety_stock": "ceil(Z * std_daily_demand * sqrt(lead_time_days))",
            "reorder_point": "ceil(mean_daily_demand * lead_time_days + safety_stock)",
            "target_stock_level": "ceil(mean_daily_demand * (lead_time_days + review_period) + safety_stock)"
        },
        "configured_parameters": {
            "default_lead_time_days": 3,
            "default_service_level": 0.95,
            "default_z_score": 1.645,
            "default_review_period_days": 7
        },
        "data_availability_audit": {
            "lead_time": "NOT_AVAILABLE in raw data (Must be user-configured or ERP supplied)",
            "holding_cost": "NOT_AVAILABLE in raw data",
            "stockout_cost": "NOT_AVAILABLE in raw data",
            "current_stock_on_hand": "NOT_AVAILABLE in sales transactions (Derived/Simulation)",
            "demand_actuals": "CONFIRMED (derived strictly from daily_product_demand.csv)"
        },
        "total_active_series_calculated": len(df_inv)
    }
    with open(reports_dir / "inventory_engine_metadata.json", "w") as f:
        json.dump(inv_metadata, f, indent=2)
    print(f"Saved inventory metadata to: {reports_dir / 'inventory_engine_metadata.json'}")
