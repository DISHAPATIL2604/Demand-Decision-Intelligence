"""
Data Cleaning & Preprocessing Pipeline Engine
Project: Demand-Decision-Intelligence

Performs data sanity checks, missing value imputation, landing price recovery logic,
and generates aggregated daily product demand for forecasting and inventory optimization.
"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def clean_and_impute_sales(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw sales transaction DataFrame:
    - Standardizes date formats
    - Imputes missing values
    - Filters out invalid negative quantities & prices
    - Recovers landing prices using product/category medians if missing
    """
    df_clean = df.copy()
    
    # 1. Date standardization
    date_col = next((c for c in df_clean.columns if c.lower() in ["date_", "date", "transaction_date"]), None)
    if date_col:
        df_clean["date_"] = pd.to_datetime(df_clean[date_col], errors="coerce")
        df_clean = df_clean.dropna(subset=["date_"])
        
    # 2. Product ID standardization
    prod_col = next((c for c in df_clean.columns if c.lower() in ["product_id", "sku", "item_id"]), None)
    if prod_col:
        df_clean["product_id"] = df_clean[prod_col].astype(str).str.strip()
        df_clean = df_clean.dropna(subset=["product_id"])
        
    # 3. Quantity Imputation & Filtering
    qty_col = next((c for c in df_clean.columns if c.lower() in ["procured_quantity", "quantity", "qty"]), None)
    if qty_col:
        df_clean["procured_quantity"] = pd.to_numeric(df_clean[qty_col], errors="coerce").fillna(1.0)
        df_clean = df_clean[df_clean["procured_quantity"] > 0]
    else:
        df_clean["procured_quantity"] = 1.0
        
    # 4. Selling Price Imputation
    price_col = next((c for c in df_clean.columns if c.lower() in ["unit_selling_price", "selling_price", "price"]), None)
    if price_col:
        df_clean["unit_selling_price"] = pd.to_numeric(df_clean[price_col], errors="coerce")
        # Impute missing price using product mean or global median
        prod_medians = df_clean.groupby("product_id")["unit_selling_price"].transform("median")
        global_median = df_clean["unit_selling_price"].median() if not df_clean["unit_selling_price"].isna().all() else 50.0
        df_clean["unit_selling_price"] = df_clean["unit_selling_price"].fillna(prod_medians).fillna(global_median)
        df_clean = df_clean[df_clean["unit_selling_price"] >= 0]
        
    # 5. Landing Price Recovery Logic
    lp_col = next((c for c in df_clean.columns if "landing" in c.lower()), None)
    if lp_col:
        df_clean["total_weighted_landing_price"] = pd.to_numeric(df_clean[lp_col], errors="coerce")
    else:
        df_clean["total_weighted_landing_price"] = np.nan
        
    # Recover landing price ratio estimate if NaN (defaulting to 75% of selling price)
    df_clean["recovered_landing_price"] = df_clean["total_weighted_landing_price"].fillna(
        df_clean["unit_selling_price"] * 0.75
    )
    
    return df_clean


def aggregate_daily_demand(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates cleaned sales transactions into daily product demand grain:
    grain: (date_, product_id, city_name)
    """
    city_col = next((c for c in df_clean.columns if "city" in c.lower()), None)
    if not city_col:
        df_clean["city_name"] = "All Cities"
    else:
        df_clean["city_name"] = df_clean[city_col]
        
    agg_df = df_clean.groupby(["date_", "product_id", "city_name"]).agg(
        daily_quantity=("procured_quantity", "sum"),
        avg_selling_price=("unit_selling_price", "mean"),
        recovered_landing_price=("recovered_landing_price", "mean")
    ).reset_index()
    
    return agg_df

if __name__ == "__main__":
    print("Data Cleaning & Preprocessing Pipeline ready.")
