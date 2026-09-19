"""
Inventory API Router
Project: Demand-Decision-Intelligence
"""

import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
import pandas as pd

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

@router.get("/recommendations")
def get_inventory_recommendations(
    product_id: Optional[str] = None,
    city_name: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """
    Returns calculated inventory optimization recommendations:
    Safety Stock, Reorder Point (ROP), Target Stock Level (TSL), and Unit Landing Cost.
    """
    sample_file = REPORTS_DIR / "inventory_decision_sample.csv"
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="Inventory recommendations dataset not found.")
        
    df = pd.read_csv(sample_file).fillna(0)
    
    if product_id:
        df = df[df["product_id"].astype(str) == str(product_id)]
    if city_name:
        df = df[df["city_name"].astype(str).str.lower() == str(city_name).lower()]
        
    res_slice = df.head(limit).to_dict(orient="records")
    return {
        "status": "success",
        "total_returned": len(res_slice),
        "data": res_slice
    }

@router.get("/metadata")
def get_inventory_metadata():
    """
    Returns inventory engine metadata and configuration audit.
    """
    meta_file = REPORTS_DIR / "inventory_engine_metadata.json"
    if not meta_file.exists():
        raise HTTPException(status_code=404, detail="Inventory metadata file not found.")
        
    with open(meta_file, "r") as f:
        data = json.load(f)
        
    return {
        "status": "success",
        "metadata": data
    }
