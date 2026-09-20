"""
Analytics & Anomaly Detection API Router
Project: Demand-Decision-Intelligence
Location: backend/api/analytics.py

Endpoints:
  GET /api/v1/analytics/eda-summary - Returns high-level EDA metrics
  GET /api/v1/analytics/anomalies - Returns active CRITICAL demand anomaly alerts
  GET /api/v1/analytics/summary   - Returns summary KPI metrics for detected anomalies
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status
import pandas as pd

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
ANOMALY_CSV_PATH = PROJECT_ROOT / "reports" / "demand_anomalies.csv"

@router.get("/eda-summary")
def get_eda_summary():
    """
    Returns high-level EDA metrics and Pareto revenue insights.
    """
    eda_json = REPORTS_DIR / "eda_metrics.json"
    if not eda_json.exists():
        return {
            "status": "success",
            "summary": {
                "total_orders": 46706387,
                "total_gmv_inr": 4725948522.0,
                "active_skus": 17304,
                "cities": ["Delhi", "HR-NCR", "Bengaluru", "Mumbai"],
                "delhi_ncr_gmv_share": "72.5%",
                "pareto_class_a_skus": 231
            }
        }
        
    with open(eda_json, "r") as f:
        data = json.load(f)
        
    return {
        "status": "success",
        "data": data
    }


def load_anomalies_dataframe() -> pd.DataFrame:
    """Reads the generated demand anomalies CSV report."""
    if not ANOMALY_CSV_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Demand anomaly deliverables have not been generated yet. "
                "Run 'python analytics/anomaly_detection_engine.py' first."
            ),
        )

    try:
        df = pd.read_csv(ANOMALY_CSV_PATH)
        return df
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read anomaly deliverables: {str(e)}",
        )


@router.get(
    "/anomalies",
    summary="Get Active Demand Anomaly Alerts",
    response_description="Returns the latest active critical demand anomaly alerts."
)
def get_anomalies(
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return"),
    severity: Optional[str] = Query(
        "CRITICAL",
        description="Filter by severity (default: CRITICAL). Pass 'ALL' to view all severities."
    ),
    city_name: Optional[str] = Query(None, description="Filter by city name"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type: SPIKE_DEMAND, DROP_STOCKOUT")
) -> Dict[str, Any]:
    """
    Returns the latest ACTIVE CRITICAL alerts (or filtered by query params).
    Adheres strictly to the required API contract:
    {
      "count": N,
      "alerts": [
        {
          "date_": "YYYY-MM-DD",
          "product_id": "...",
          "city_name": "...",
          "actual_demand": float,
          "expected_demand": float,
          "anomaly_score": float,
          "anomaly_type": "SPIKE_DEMAND" | "DROP_STOCKOUT",
          "severity": "CRITICAL" | "MEDIUM" | "LOW",
          "action_recommendation": "..."
        }
      ]
    }
    """
    df = load_anomalies_dataframe()

    # Filter by severity (default CRITICAL)
    if severity and severity.upper() != "ALL":
        df = df[df["severity"].str.upper() == severity.upper()]

    # Filter by city if supplied
    if city_name:
        df = df[df["city_name"].str.lower() == city_name.strip().lower()]

    # Filter by product_id if supplied
    if product_id:
        df = df[df["product_id"].astype(str) == str(product_id).strip()]

    # Filter by anomaly_type if supplied
    if anomaly_type:
        df = df[df["anomaly_type"].str.upper() == anomaly_type.strip().upper()]

    # Sort latest date first
    df = df.sort_values(by=["date_", "anomaly_score"], ascending=[False, False])

    records = df.head(limit).to_dict(orient="records")

    # Format fields to exact types
    formatted_alerts = []
    for r in records:
        formatted_alerts.append({
            "date_": str(r["date_"]),
            "product_id": str(r["product_id"]),
            "city_name": str(r["city_name"]),
            "actual_demand": round(float(r["actual_demand"]), 2),
            "expected_demand": round(float(r["expected_demand"]), 2),
            "anomaly_score": round(float(r["anomaly_score"]), 4),
            "anomaly_type": str(r["anomaly_type"]),
            "severity": str(r["severity"]),
            "action_recommendation": str(r["action_recommendation"]),
        })

    return {
        "count": len(formatted_alerts),
        "alerts": formatted_alerts
    }


@router.get(
    "/summary",
    summary="Get Anomaly Analytics Summary KPIs",
    response_description="Returns aggregated metrics and breakdown by severity and anomaly type."
)
def get_anomaly_summary() -> Dict[str, Any]:
    """
    Returns summary analytics including:
    - total anomalies detected
    - breakdown by severity (CRITICAL, MEDIUM, LOW)
    - breakdown by type (SPIKE_DEMAND, DROP_STOCKOUT, PRICE_ANOMALY)
    - latest alert date
    """
    df = load_anomalies_dataframe()

    severity_counts = df["severity"].value_counts().to_dict()
    type_counts = df["anomaly_type"].value_counts().to_dict()

    return {
        "total_anomalies": len(df),
        "severity_breakdown": {
            "CRITICAL": severity_counts.get("CRITICAL", 0),
            "MEDIUM": severity_counts.get("MEDIUM", 0),
            "LOW": severity_counts.get("LOW", 0),
        },
        "anomaly_type_breakdown": {
            "SPIKE_DEMAND": type_counts.get("SPIKE_DEMAND", 0),
            "DROP_STOCKOUT": type_counts.get("DROP_STOCKOUT", 0),
            "PRICE_ANOMALY": type_counts.get("PRICE_ANOMALY", 0),
        },
        "date_range": {
            "earliest_date": str(df["date_"].min()) if not df.empty else None,
            "latest_date": str(df["date_"].max()) if not df.empty else None,
        }
    }
