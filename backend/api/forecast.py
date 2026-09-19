"""
Forecast API Router
Project: Demand-Decision-Intelligence
"""

import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
import pandas as pd

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

@router.get("/evaluation")
def get_forecast_evaluation():
    """
    Returns the comparative evaluation metrics (MAE, RMSE, WAPE)
    for all 8 benchmark models evaluated in Stage S3.
    """
    comp_file = REPORTS_DIR / "model_comparison.csv"
    eval_json_file = REPORTS_DIR / "forecast_evaluation_report.json"
    
    if not comp_file.exists():
        raise HTTPException(status_code=440, detail="Evaluation results not generated yet.")
        
    df_comp = pd.read_csv(comp_file)
    models = df_comp.to_dict(orient="records")
    
    extra_meta = {}
    if eval_json_file.exists():
        with open(eval_json_file, "r") as f:
            extra_meta = json.load(f)
            
    return {
        "status": "success",
        "best_model": models[0]["model"] if models else "Prophet (Weekly Seasonality)",
        "models": models,
        "metadata": extra_meta
    }

@router.get("/results")
def get_forecast_results(
    product_id: Optional[str] = None,
    city_name: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
):
    """
    Returns actual vs predicted demand data across models.
    """
    results_file = REPORTS_DIR / "forecast_results.csv"
    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Forecast results file not found.")
        
    df = pd.read_csv(results_file)
    
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
