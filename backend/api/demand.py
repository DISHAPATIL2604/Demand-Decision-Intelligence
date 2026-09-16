import json
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

router = APIRouter()

project_root = Path(__file__).resolve().parent.parent.parent
reports_dir = project_root / "reports"

@router.get("/summary", summary="Get Demand Intelligence Dataset Summary")
def get_demand_summary():
    """Returns dataset dimensions, date coverage, and forensic status."""
    return {
        "dataset_name": "Flipkart Grocery Demand Intelligence",
        "total_sales_transactions": 46_706_387,
        "total_demand_quantity": 60_176_096,
        "total_revenue_inr": 4_725_948_522.0,
        "date_range": {
            "start": "2022-04-01",
            "end": "2022-07-10",
            "total_calendar_days": 101,
            "recorded_active_days": 81
        },
        "geography": ["Bengaluru", "Delhi", "HR-NCR", "Mumbai"],
        "catalog": {
            "total_product_master_skus": 32_226,
            "active_sales_skus": 17_304,
            "product_city_series": 46_305,
            "unmatched_skus": 1_496,
            "unmatched_sales_rows": 532_122,
            "match_rate_pct": 98.86
        },
        "data_integrity": {
            "fabricated_rows": 0,
            "deleted_rows": 0,
            "unmatched_attributes_status": "NOT_AVAILABLE"
        }
    }

@router.get("/forecast-metrics", summary="Get Forecasting Model Benchmarks and Error Analysis")
def get_forecast_metrics():
    """Returns time-based validation performance across baselines and ML models."""
    metrics_file = reports_dir / "forecast_evaluation_report.json"
    if not metrics_file.exists():
        raise HTTPException(status_code=404, detail="Forecast evaluation metrics report not found.")
    with open(metrics_file, "r") as f:
        return json.load(f)

@router.get("/inventory-recommendations", summary="Get Safety Stock and Reorder Point Recommendations")
def get_inventory_recommendations(
    limit: int = Query(50, ge=1, le=1000),
    city: Optional[str] = Query(None, description="Filter by city name"),
    lead_time_days: int = Query(3, ge=1, le=30),
    service_level: float = Query(0.95, ge=0.80, le=0.99)
):
    """
    Returns inventory policies (Safety Stock, ROP, Target Stock Level).
    Note: Lead time and service level are user-supplied configuration parameters.
    """
    import pandas as pd
    sample_file = reports_dir / "inventory_decision_sample.csv"
    if not sample_file.exists():
        raise HTTPException(status_code=404, detail="Inventory decision recommendations not generated.")
    
    df = pd.read_csv(sample_file)
    if city:
        df = df[df["city_name"].str.lower() == city.lower()]
    
    # Recalculate dynamic columns if parameters differ from default
    if lead_time_days != 3 or service_level != 0.95:
        z_scores = {0.90: 1.282, 0.95: 1.645, 0.98: 2.054, 0.99: 2.326}
        z = z_scores.get(round(service_level, 2), 1.645)
        import numpy as np
        df["lead_time_days_param"] = lead_time_days
        df["target_service_level_param"] = service_level
        df["safety_stock"] = np.ceil(z * df["std_daily_demand"] * np.sqrt(lead_time_days)).astype(int)
        df["reorder_point"] = np.ceil(df["mean_daily_demand"] * lead_time_days + df["safety_stock"]).astype(int)
        df["target_stock_level"] = np.ceil(df["mean_daily_demand"] * (lead_time_days + 7) + df["safety_stock"]).astype(int)
        
    records = df.head(limit).to_dict(orient="records")
    return {
        "parameters": {
            "lead_time_days": lead_time_days,
            "target_service_level": service_level,
            "review_period_days": 7
        },
        "total_results": len(records),
        "data": records
    }
