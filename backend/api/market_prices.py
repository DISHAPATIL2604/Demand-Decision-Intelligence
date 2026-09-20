"""
backend/api/market_prices.py
----------------------------
FastAPI Router for Real-World Government Market Price Monitoring & Stocking Intelligence.
Endpoints:
  GET  /api/market-prices/live
  GET  /api/market-prices/stock-decisions
  POST /api/market-prices/sync
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, Query

from backend.services.market_price_scraper import fetch_live_commodity_prices
from backend.services.price_intelligence import generate_market_stock_decisions

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/live", summary="Get Live Government PMD Commodity Rates")
def get_live_market_prices(
    category: str = Query(None, description="Filter by category: 'Grains & Pulses', 'Edible Oils', 'Vegetables', 'Daily Essentials'")
) -> Dict[str, Any]:
    """
    Returns real-time daily retail prices across 22 essential commodities
    scraped directly from the Ministry of Consumer Affairs portal (fcainfoweb.nic.in).
    """
    data = fetch_live_commodity_prices(force_refresh=False)
    if category and category.upper() != "ALL":
        filtered = [c for c in data.get("commodities", []) if c["category"].lower() == category.lower()]
        data = {**data, "commodities": filtered, "total_commodities": len(filtered)}
    return data


@router.get("/stock-decisions", summary="Get Real-World Price Impact & Stocking Recommendations")
def get_market_stock_decisions() -> Dict[str, Any]:
    """
    Evaluates live market commodity inflation/deflation vs catalog baselines
    and outputs quantity holding recommendations (trim vs bulk purchase).
    """
    return generate_market_stock_decisions(force_refresh=False)


@router.post("/sync", summary="Trigger Instant Live Scrape of Government Portal")
def trigger_market_prices_sync() -> Dict[str, Any]:
    """
    Forces an immediate live HTTP fetch of fcainfoweb.nic.in to sync the latest daily prices.
    """
    fresh_data = fetch_live_commodity_prices(force_refresh=True)
    fresh_decisions = generate_market_stock_decisions(force_refresh=True)
    return {
        "status": "success",
        "message": "Successfully synchronized live rates with Ministry of Consumer Affairs portal.",
        "as_on_date": fresh_data.get("as_on_date"),
        "total_commodities": fresh_data.get("total_commodities"),
        "total_evaluated_skus": fresh_decisions.get("total_evaluated_skus"),
    }
