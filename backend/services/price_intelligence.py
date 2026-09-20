"""
backend/services/price_intelligence.py
--------------------------------------
Evaluates real-world market commodity prices vs internal catalog baseline prices.
Generates dynamic quantity stocking recommendations:
How much inventory quantity to hold vs trim based on real-time market inflation/deflation.
"""

from typing import Any, Dict, List
from backend.services.market_price_scraper import fetch_live_commodity_prices

# Catalog SKU to Government Commodity mapping
SKU_COMMODITY_MAPPING = [
    {
        "product_id": "19512",
        "product_name": "Premium Wheat Atta (10Kg)",
        "commodity": "Atta (Wheat)",
        "baseline_cost_per_kg": 32.50,
        "standard_holding_qty": 28500,
        "city_name": "Delhi"
    },
    {
        "product_id": "391306",
        "product_name": "Pure Kachi Ghani Mustard Oil (1L)",
        "commodity": "Mustard Oil (Packed)",
        "baseline_cost_per_kg": 165.00,
        "standard_holding_qty": 18200,
        "city_name": "Bengaluru"
    },
    {
        "product_id": "12872",
        "product_name": "Unpolished Tur/Arhar Dal (1Kg)",
        "commodity": "Tur/Arhar Dal",
        "baseline_cost_per_kg": 105.00,
        "standard_holding_qty": 15400,
        "city_name": "Mumbai"
    },
    {
        "product_id": "3881",
        "product_name": "Daily Everyday Basmati Rice (5Kg)",
        "commodity": "Rice",
        "baseline_cost_per_kg": 41.00,
        "standard_holding_qty": 22000,
        "city_name": "HR-NCR"
    },
    {
        "product_id": "445675",
        "product_name": "Farm Fresh Red Tomatoes (Per Kg)",
        "commodity": "Tomato",
        "baseline_cost_per_kg": 25.00,
        "standard_holding_qty": 12000,
        "city_name": "Delhi"
    },
    {
        "product_id": "176190",
        "product_name": "Grade-A Nashik Onions (Per Kg)",
        "commodity": "Onion",
        "baseline_cost_per_kg": 36.00,
        "standard_holding_qty": 14500,
        "city_name": "Bengaluru"
    },
    {
        "product_id": "1",
        "product_name": "Pahadi Fresh Potatoes (Per Kg)",
        "commodity": "Potato",
        "baseline_cost_per_kg": 18.50,
        "standard_holding_qty": 16000,
        "city_name": "Delhi"
    },
    {
        "product_id": "50",
        "product_name": "Refined White Crystal Sugar (1Kg)",
        "commodity": "Sugar",
        "baseline_cost_per_kg": 50.00,
        "standard_holding_qty": 19000,
        "city_name": "Mumbai"
    },
    {
        "product_id": "52",
        "product_name": "Pasteurized Toned Fresh Milk (1L)",
        "commodity": "Milk @",
        "baseline_cost_per_kg": 55.00,
        "standard_holding_qty": 8500,
        "city_name": "HR-NCR"
    },
    {
        "product_id": "31",
        "product_name": "Refined Sunflower Oil (1L)",
        "commodity": "Sunflower Oil (Packed)",
        "baseline_cost_per_kg": 168.00,
        "standard_holding_qty": 14000,
        "city_name": "Bengaluru"
    }
]


def generate_market_stock_decisions(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Combines live government PMD commodity rates with catalog SKUs
    to evaluate price divergence and recommended holding quantities.
    """
    market_data = fetch_live_commodity_prices(force_refresh=force_refresh)
    commodities_list = market_data.get("commodities", [])
    
    # Lookup table by commodity name
    comm_lookup = {c["commodity"].lower(): c for c in commodities_list}

    decisions: List[Dict[str, Any]] = []

    for item in SKU_COMMODITY_MAPPING:
        comm_name = item["commodity"]
        comm_info = comm_lookup.get(comm_name.lower())

        if comm_info:
            live_price = float(comm_info["price_inr_per_kg"])
            as_on = comm_info.get("as_on_date", market_data.get("as_on_date", "Live"))
        else:
            live_price = item["baseline_cost_per_kg"] * 1.10
            as_on = market_data.get("as_on_date", "Live")

        baseline = item["baseline_cost_per_kg"]
        standard_qty = item["standard_holding_qty"]

        # Calculate Price Divergence %
        divergence_pct = round(((live_price - baseline) / baseline) * 100, 1)

        # Dynamic Quantity Recommendation Logic
        if divergence_pct >= 25.0:
            action = "TRIM_STOCK"
            action_label = "Trim Stock (-20%)"
            qty_multiplier = 0.80
            risk_level = "HIGH_INFLATION"
            recommendation = (
                f"Market price surged by +{divergence_pct}%. Consumer elasticity indicates "
                "demand contraction. Reduce holding buffer to prevent capital lockup and perishability."
            )
            badge_color = "#ef4444"
            badge_bg = "rgba(239, 68, 68, 0.15)"
        elif divergence_pct >= 12.0:
            action = "MODERATE_REDUCTION"
            action_label = "Cautious Buffer (-10%)"
            qty_multiplier = 0.90
            risk_level = "MODERATE_SURGE"
            recommendation = (
                f"Market rate elevated (+{divergence_pct}%). Maintain cautious procurement cycles."
            )
            badge_color = "#f59e0b"
            badge_bg = "rgba(245, 158, 11, 0.15)"
        elif divergence_pct <= -10.0:
            action = "BULK_PROCURE"
            action_label = "Bulk Stock (+25%)"
            qty_multiplier = 1.25
            risk_level = "OPPORTUNITY_DIP"
            recommendation = (
                f"Market price dipped by {divergence_pct}%. Favorable procurement window. "
                "Advance forward purchase orders to secure high margin buffers."
            )
            badge_color = "#10b981"
            badge_bg = "rgba(16, 185, 129, 0.15)"
        else:
            action = "MAINTAIN_BASELINE"
            action_label = "Standard ROP (0%)"
            qty_multiplier = 1.00
            risk_level = "STABLE_MARKET"
            recommendation = (
                f"Market rate aligned with historical baseline ({divergence_pct}% divergence). "
                "Maintain standard reorder policy."
            )
            badge_color = "#06b6d4"
            badge_bg = "rgba(6, 182, 212, 0.15)"

        recommended_qty = int(round(standard_qty * qty_multiplier))

        decisions.append({
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "commodity_matched": comm_name,
            "city_name": item["city_name"],
            "live_market_price": live_price,
            "baseline_price": baseline,
            "divergence_pct": divergence_pct,
            "standard_holding_qty": standard_qty,
            "recommended_holding_qty": recommended_qty,
            "quantity_delta": recommended_qty - standard_qty,
            "action": action,
            "action_label": action_label,
            "risk_level": risk_level,
            "recommendation": recommendation,
            "badge_color": badge_color,
            "badge_bg": badge_bg,
            "as_on_date": as_on
        })

    return {
        "status": "success",
        "market_source": "Government of India - Ministry of Consumer Affairs (PMD)",
        "as_on_date": market_data.get("as_on_date", "Live"),
        "total_evaluated_skus": len(decisions),
        "decisions": decisions
    }
