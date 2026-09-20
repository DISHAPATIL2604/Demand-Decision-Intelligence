"""
Inventory API Router
Project: Demand-Decision-Intelligence
Provides inventory recommendations, dynamic policy calculations,
and daily simulation status (Closing Stock = Opening + Received - Sales).
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.session import get_db
from backend.models.inventory import InventoryState, InventoryRecommendation
from backend.models.product import Product

router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


@router.get("/status")
def get_inventory_status(
    product_id: Optional[str] = None,
    city_name: Optional[str] = None,
    snapshot_date: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Returns daily inventory simulation status:
    Formula: Closing Stock = Opening Stock + Stock Received - Sales Quantity.
    Includes Days of Stock Cover, stockout risk indicators, and reorder urgency.
    """
    query = db.query(InventoryState).join(Product, InventoryState.product_id == Product.product_id, isouter=True)

    if product_id:
        try:
            pid_int = int(product_id)
            query = query.filter(InventoryState.product_id == pid_int)
        except ValueError:
            pass

    if city_name and city_name.upper() != "ALL":
        query = query.filter(InventoryState.city_name.ilike(city_name.strip()))

    if snapshot_date:
        try:
            parsed_d = date.fromisoformat(snapshot_date.strip())
            query = query.filter(InventoryState.snapshot_date == parsed_d)
        except ValueError:
            pass

    rows = query.order_by(InventoryState.snapshot_date.desc(), InventoryState.product_id).limit(limit).all()

    # Pre-fetch recommendation averages for days-of-cover computation
    rec_dict = {}
    if rows:
        p_ids = {r.product_id for r in rows}
        recs = db.query(InventoryRecommendation).filter(InventoryRecommendation.product_id.in_(p_ids)).all()
        for r in recs:
            rec_dict[(r.product_id, r.city_name)] = r.avg_daily_demand

    results = []
    for item in rows:
        daily_dem = rec_dict.get((item.product_id, item.city_name), max(1.0, item.sales_quantity))
        days_cover = round(item.closing_stock / max(1.0, daily_dem), 1)

        if days_cover <= 2.0:
            stockout_risk = "CRITICAL_STOCKOUT"
            reorder_urgency = "HIGH"
            action_text = "Trigger Emergency Replenishment"
        elif days_cover <= 4.0:
            stockout_risk = "REORDER_RECOMMENDED"
            reorder_urgency = "MEDIUM"
            action_text = "Issue Supplier Reorder"
        elif days_cover > 15.0:
            stockout_risk = "OVERSTOCK"
            reorder_urgency = "LOW"
            action_text = "Surplus Inventory - Pause PO"
        else:
            stockout_risk = "OPTIMAL"
            reorder_urgency = "NONE"
            action_text = "Stock Buffer Adequate"

        results.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": item.product.product_name if item.product else f"SKU #{item.product_id}",
            "city_name": item.city_name,
            "snapshot_date": str(item.snapshot_date),
            "opening_stock": round(item.opening_stock, 1),
            "stock_received": round(item.stock_received, 1),
            "sales_quantity": round(item.sales_quantity, 1),
            "closing_stock": round(item.closing_stock, 1),
            "is_simulated": item.is_simulated,
            "days_of_cover": days_cover,
            "stockout_risk": stockout_risk,
            "reorder_urgency": reorder_urgency,
            "action_text": action_text,
        })

    return {
        "status": "success",
        "total_returned": len(results),
        "data": results
    }


@router.get("/recommendations")
def get_inventory_recommendations(
    product_id: Optional[str] = None,
    city_name: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    db: Session = Depends(get_db)
):
    """
    Returns calculated inventory optimization recommendations:
    Safety Stock, Reorder Point (ROP), Target Stock Level (TSL), and Unit Landing Cost.
    Queries the PostgreSQL database inventory_recommendations table with CSV fallback.
    """
    db_query = db.query(InventoryRecommendation).join(
        Product, InventoryRecommendation.product_id == Product.product_id, isouter=True
    )

    if product_id:
        try:
            pid_int = int(product_id)
            db_query = db_query.filter(InventoryRecommendation.product_id == pid_int)
        except ValueError:
            pass

    if city_name and city_name.upper() != "ALL":
        db_query = db_query.filter(InventoryRecommendation.city_name.ilike(city_name.strip()))

    db_recs = db_query.order_by(desc(InventoryRecommendation.avg_daily_demand)).limit(limit).all()

    if db_recs:
        res_list = []
        for r in db_recs:
            res_list.append({
                "id": r.id,
                "product_id": r.product_id,
                "product_name": r.product.product_name if r.product else f"Product #{r.product_id}",
                "city_name": r.city_name,
                "calculation_date": str(r.calculation_date),
                "current_stock": r.current_stock,
                "mean_daily_demand": r.avg_daily_demand,
                "avg_daily_demand": r.avg_daily_demand,
                "std_daily_demand": round(r.avg_daily_demand * 0.12, 2),
                "lead_time_days": r.lead_time_days,
                "safety_stock": r.safety_stock,
                "reorder_point": r.reorder_point,
                "target_stock_level": round(r.reorder_point + (r.avg_daily_demand * 7), 1),
                "recommended_order_qty": r.recommended_order_qty,
                "risk_status": r.risk_status,
                "priority": r.priority,
            })
        return {
            "status": "success",
            "source": "database",
            "total_returned": len(res_list),
            "data": res_list
        }

    # Fallback to report CSV
    sample_file = REPORTS_DIR / "inventory_decision_sample.csv"
    if sample_file.exists():
        import pandas as pd
        df = pd.read_csv(sample_file).fillna(0)
        if product_id:
            df = df[df["product_id"].astype(str) == str(product_id)]
        if city_name and city_name.upper() != "ALL":
            df = df[df["city_name"].astype(str).str.lower() == str(city_name).lower()]
        res_slice = df.head(limit).to_dict(orient="records")
        return {
            "status": "success",
            "source": "csv_fallback",
            "total_returned": len(res_slice),
            "data": res_slice
        }

    return {
        "status": "success",
        "source": "empty",
        "total_returned": 0,
        "data": []
    }


@router.get("/metadata")
def get_inventory_metadata():
    """
    Returns inventory engine metadata and configuration audit.
    """
    meta_file = REPORTS_DIR / "inventory_engine_metadata.json"
    if not meta_file.exists():
        return {
            "status": "success",
            "metadata": {
                "engine_version": "2.1.0",
                "default_lead_time_days": 3,
                "target_service_level": 0.95,
                "review_period_days": 7
            }
        }

    with open(meta_file, "r") as f:
        data = json.load(f)

    return {
        "status": "success",
        "metadata": data
    }
