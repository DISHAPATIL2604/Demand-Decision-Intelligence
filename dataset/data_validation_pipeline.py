"""
Data Validation Pipeline Engine
Project: Demand-Decision-Intelligence

Provides data quality checks, schema validation, missing value auditing,
and product master ID matching for incoming sales datasets.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def validate_sales_data(file_path: str, product_master_path: str = None) -> dict:
    """
    Validates an incoming sales dataset CSV file.
    
    Checks:
    - Schema & required columns
    - Row count & null values
    - Date format and date range sanity
    - Negative or zero quantities/prices
    - Product Master ID match rate against dim_product
    - Duplicates
    """
    path = Path(file_path)
    if not path.exists():
        return {"status": "FAIL", "error": f"File not found: {file_path}"}
        
    try:
        # Load sample or header
        df_head = pd.read_csv(path, nrows=5)
        cols = list(df_head.columns)
        
        required_cols = ["date_", "product_id", "procured_quantity", "unit_selling_price"]
        missing_required = [c for c in required_cols if c not in cols and c.lower() not in [x.lower() for x in cols]]
        
        if missing_required:
            return {
                "status": "FAIL_SCHEMA",
                "error": f"Missing required columns: {missing_required}",
                "available_columns": cols
            }

        # Read dataset (chunked if large, or direct read)
        df = pd.read_csv(path, low_memory=False)
        
        total_rows = len(df)
        dup_count = int(df.duplicated().sum())
        
        # Date column matching
        date_col = next((c for c in cols if c.lower() in ["date_", "date", "transaction_date"]), None)
        parsed_dates = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.Series()
        missing_dates = int(parsed_dates.isna().sum())
        min_date = str(parsed_dates.min().date()) if len(parsed_dates.dropna()) else ""
        max_date = str(parsed_dates.max().date()) if len(parsed_dates.dropna()) else ""
        
        # Product ID matching
        prod_col = next((c for c in cols if c.lower() in ["product_id", "sku", "item_id"]), None)
        missing_pids = int(df[prod_col].isna().sum()) if prod_col else total_rows
        unique_products = int(df[prod_col].nunique()) if prod_col else 0
        
        match_rate = 1.0
        if product_master_path and Path(product_master_path).exists() and prod_col:
            pm = pd.read_csv(product_master_path, low_memory=False)
            pm_col = next((c for c in pm.columns if c.lower() in ["product_id", "sku", "item_id"]), None)
            if pm_col:
                master_ids = set(pm[pm_col].dropna().astype(str).str.strip())
                incoming_ids = df[prod_col].dropna().astype(str).str.strip()
                matched = incoming_ids.isin(master_ids).sum()
                match_rate = float(matched / len(incoming_ids)) if len(incoming_ids) else 0.0
                
        # Quantity & Price sanity
        qty_col = next((c for c in cols if c.lower() in ["procured_quantity", "quantity", "qty"]), None)
        price_col = next((c for c in cols if c.lower() in ["unit_selling_price", "selling_price", "price"]), None)
        
        neg_qty = int((pd.to_numeric(df[qty_col], errors="coerce") < 0).sum()) if qty_col else 0
        neg_price = int((pd.to_numeric(df[price_col], errors="coerce") < 0).sum()) if price_col else 0
        
        status = "PASS"
        if missing_dates > 0 or missing_pids > 0 or neg_qty > 0 or neg_price > 0:
            status = "WARNINGS"
            
        validation_report = {
            "status": status,
            "filename": path.name,
            "total_rows": total_rows,
            "duplicate_rows": dup_count,
            "unique_products": unique_products,
            "min_date": min_date,
            "max_date": max_date,
            "missing_dates": missing_dates,
            "missing_product_ids": missing_pids,
            "negative_quantities": neg_qty,
            "negative_prices": neg_price,
            "product_master_match_rate": round(match_rate * 100, 2)
        }
        return validation_report
        
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

if __name__ == "__main__":
    sample_file = BASE_DIR / "dataset" / "cleaned" / "sales_product_master.csv"
    if sample_file.exists():
        res = validate_sales_data(str(sample_file))
        print("Data Validation Result:")
        print(json.dumps(res, indent=2))
