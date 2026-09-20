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
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
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
    response_description="Returns the latest active critical demand anomaly alerts from DB or CSV."
)
def get_anomalies(
    limit: int = Query(50, ge=1, le=500, description="Max alerts to return"),
    severity: Optional[str] = Query(
        "CRITICAL",
        description="Filter by severity (default: CRITICAL). Pass 'ALL' to view all severities."
    ),
    city_name: Optional[str] = Query(None, description="Filter by city name"),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    anomaly_type: Optional[str] = Query(None, description="Filter by anomaly type: SPIKE_DEMAND, DROP_STOCKOUT"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns the latest ACTIVE CRITICAL alerts from PostgreSQL anomalies table,
    falling back to CSV if database has no records.
    """
    # Try PostgreSQL first
    db_query = db.query(AnomalyAlert)
    if severity and severity.upper() != "ALL":
        db_query = db_query.filter(AnomalyAlert.severity == severity.upper())
    if city_name and city_name.upper() != "ALL":
        db_query = db_query.filter(AnomalyAlert.city_name.ilike(city_name.strip()))
    if product_id:
        try:
            pid_int = int(product_id)
            db_query = db_query.filter(AnomalyAlert.product_id == pid_int)
        except ValueError:
            pass
    if anomaly_type and anomaly_type.upper() != "ALL":
        db_query = db_query.filter(AnomalyAlert.anomaly_type.ilike(anomaly_type.strip()))

    db_alerts = db_query.order_by(desc(AnomalyAlert.anomaly_date), desc(AnomalyAlert.id)).limit(limit).all()

    if db_alerts:
        formatted = [
            {
                "id": a.id,
                "date_": str(a.anomaly_date),
                "product_id": str(a.product_id),
                "city_name": a.city_name,
                "actual_demand": round(a.actual_value, 2),
                "expected_demand": round(a.expected_value or 0.0, 2),
                "anomaly_score": round(abs(a.actual_value - (a.expected_value or a.actual_value)) / max(1.0, a.expected_value or a.actual_value), 4),
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "action_recommendation": a.description or "Review demand shift and inventory buffer.",
                "status": a.status,
            }
            for a in db_alerts
        ]
        return {
            "source": "database",
            "count": len(formatted),
            "alerts": formatted
        }

    # CSV Fallback
    df = load_anomalies_dataframe()
    if df.empty:
        return {"source": "empty", "count": 0, "alerts": []}

    if severity and severity.upper() != "ALL":
        df = df[df["severity"].str.upper() == severity.upper()]
    if city_name and city_name.upper() != "ALL":
        df = df[df["city_name"].str.lower() == city_name.strip().lower()]
    if product_id:
        df = df[df["product_id"].astype(str) == str(product_id).strip()]
    if anomaly_type and anomaly_type.upper() != "ALL":
        df = df[df["anomaly_type"].str.upper() == anomaly_type.strip().upper()]

    df = df.sort_values(by=["date_", "anomaly_score"], ascending=[False, False])
    records = df.head(limit).to_dict(orient="records")

    formatted_alerts = [
        {
            "date_": str(r["date_"]),
            "product_id": str(r["product_id"]),
            "city_name": str(r["city_name"]),
            "actual_demand": round(float(r["actual_demand"]), 2),
            "expected_demand": round(float(r["expected_demand"]), 2),
            "anomaly_score": round(float(r["anomaly_score"]), 4),
            "anomaly_type": str(r["anomaly_type"]),
            "severity": str(r["severity"]),
            "action_recommendation": str(r["action_recommendation"]),
            "status": "OPEN",
        }
        for r in records
    ]

    return {
        "source": "csv_fallback",
        "count": len(formatted_alerts),
        "alerts": formatted_alerts
    }


@router.get(
    "/summary",
    summary="Get Anomaly Analytics Summary KPIs",
    response_description="Returns aggregated metrics and breakdown by severity and anomaly type."
)
def get_anomaly_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns summary analytics from DB or CSV.
    """
    db_count = db.query(AnomalyAlert).count()
    if db_count > 0:
        crit = db.query(AnomalyAlert).filter(AnomalyAlert.severity == "CRITICAL").count()
        med = db.query(AnomalyAlert).filter(AnomalyAlert.severity == "MEDIUM").count()
        low = db.query(AnomalyAlert).filter(AnomalyAlert.severity == "LOW").count()

        spike = db.query(AnomalyAlert).filter(AnomalyAlert.anomaly_type.like("%SPIKE%")).count()
        drop_ = db.query(AnomalyAlert).filter(AnomalyAlert.anomaly_type.like("%DROP%")).count()
        price = db.query(AnomalyAlert).filter(AnomalyAlert.anomaly_type.like("%PRICE%")).count()

        min_d = db.query(func.min(AnomalyAlert.anomaly_date)).scalar()
        max_d = db.query(func.max(AnomalyAlert.anomaly_date)).scalar()

        return {
            "source": "database",
            "total_anomalies": db_count,
            "severity_breakdown": {
                "CRITICAL": crit,
                "MEDIUM": med,
                "LOW": low,
            },
            "anomaly_type_breakdown": {
                "SPIKE_DEMAND": spike,
                "DROP_STOCKOUT": drop_,
                "PRICE_ANOMALY": price,
            },
            "date_range": {
                "earliest_date": str(min_d) if min_d else None,
                "latest_date": str(max_d) if max_d else None,
            }
        }

    df = load_anomalies_dataframe()
    if df.empty:
        return {
            "total_anomalies": 0,
            "severity_breakdown": {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0},
            "anomaly_type_breakdown": {"SPIKE_DEMAND": 0, "DROP_STOCKOUT": 0, "PRICE_ANOMALY": 0},
            "date_range": {"earliest_date": None, "latest_date": None}
        }

    severity_counts = df["severity"].value_counts().to_dict()
    type_counts = df["anomaly_type"].value_counts().to_dict()

    return {
        "source": "csv_fallback",
        "total_anomalies": len(df),
        "severity_breakdown": {
            "CRITICAL": int(severity_counts.get("CRITICAL", 0)),
            "MEDIUM": int(severity_counts.get("MEDIUM", 0)),
            "LOW": int(severity_counts.get("LOW", 0)),
        },
        "anomaly_type_breakdown": {
            "SPIKE_DEMAND": int(type_counts.get("SPIKE_DEMAND", 0)),
            "DROP_STOCKOUT": int(type_counts.get("DROP_STOCKOUT", 0)),
            "PRICE_ANOMALY": int(type_counts.get("PRICE_ANOMALY", 0)),
        },
        "date_range": {
            "earliest_date": str(df["date_"].min()) if not df.empty else None,
            "latest_date": str(df["date_"].max()) if not df.empty else None,
        }
    }
