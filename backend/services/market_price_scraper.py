"""
backend/services/market_price_scraper.py
----------------------------------------
Scrapes real-time commodity prices from the official Government of India portal:
Ministry of Consumer Affairs, Food and Public Distribution - Price Monitoring Division (PMD)
URL: https://fcainfoweb.nic.in/Default.aspx
"""

import json
import logging
import re
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
CACHE_FILE = REPORTS_DIR / "live_market_prices.json"

FCA_URL = "https://fcainfoweb.nic.in/Default.aspx"

# Category mapping based on PMD GridView layouts
CATEGORY_MAPPING = {
    "Rice": "Grains & Pulses",
    "Wheat": "Grains & Pulses",
    "Atta (Wheat)": "Grains & Pulses",
    "Gram Dal": "Grains & Pulses",
    "Tur/Arhar Dal": "Grains & Pulses",
    "Urad Dal": "Grains & Pulses",
    "Moong Dal": "Grains & Pulses",
    "Masoor Dal": "Grains & Pulses",
    "Broken Rice": "Grains & Pulses",
    "Groundnut Oil (Packed)": "Edible Oils",
    "Mustard Oil (Packed)": "Edible Oils",
    "Vanaspati (Packed)": "Edible Oils",
    "Soya Oil (Packed)": "Edible Oils",
    "Sunflower Oil (Packed)": "Edible Oils",
    "Palm Oil (Packed)": "Edible Oils",
    "Potato": "Vegetables",
    "Onion": "Vegetables",
    "Tomato": "Vegetables",
    "Sugar": "Daily Essentials",
    "Gur": "Daily Essentials",
    "Milk @": "Daily Essentials",
    "Tea Loose": "Daily Essentials",
    "Salt Pack (Iodised)": "Daily Essentials",
    "Bajra (whole)": "Additional Millets",
    "Jowar (whole)": "Additional Millets",
    "Ragi": "Additional Millets",
    "Maize": "Additional Millets",
    "Barley": "Additional Millets",
}


def fetch_live_commodity_prices(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Fetches real-time commodity prices from fcainfoweb.nic.in.
    Falls back to cached JSON if portal is slow or unreachable.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Attempt live scrape
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        }

        req = urllib.request.Request(FCA_URL, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        date_match = re.search(r'id="lblDate1">([^<]+)<', html)
        as_on_date = date_match.group(1).strip() if date_match else datetime.now().strftime("%d/%m/%Y")

        comm_names = re.findall(r'lblCommName">([^<]+)<', html)
        prices = re.findall(r'lblPrices">([0-9.]+)<', html)

        if comm_names and prices:
            items: List[Dict[str, Any]] = []
            seen = set()
            for name, price in zip(comm_names, prices):
                clean_name = name.strip()
                if clean_name in seen:
                    continue
                seen.add(clean_name)
                category = CATEGORY_MAPPING.get(clean_name, "Grains & Essentials")
                items.append({
                    "commodity": clean_name,
                    "price_inr_per_kg": float(price),
                    "category": category,
                    "unit": "₹ / Kg",
                    "as_on_date": as_on_date,
                    "source": "Ministry of Consumer Affairs, Food and Public Distribution (PMD)"
                })

            result = {
                "status": "live",
                "as_on_date": as_on_date,
                "fetched_at": datetime.now().isoformat(),
                "total_commodities": len(items),
                "source_url": FCA_URL,
                "commodities": items
            }

            # Save to cache
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully scraped {len(items)} commodities from PMD portal.")
            return result

    except Exception as e:
        logger.warning(f"Live scrape failed ({str(e)}), attempting cache fallback.")

    # 2. Fallback to cache if scrape failed
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                cached["status"] = "cached"
                return cached
        except Exception:
            pass

    # 3. Default fallback data if first run and offline
    default_items = [
        {"commodity": "Rice", "price_inr_per_kg": 46.11, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Wheat", "price_inr_per_kg": 31.87, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Atta (Wheat)", "price_inr_per_kg": 37.52, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Gram Dal", "price_inr_per_kg": 88.23, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Tur/Arhar Dal", "price_inr_per_kg": 124.43, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Urad Dal", "price_inr_per_kg": 122.63, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Moong Dal", "price_inr_per_kg": 112.03, "category": "Grains & Pulses", "unit": "₹ / Kg"},
        {"commodity": "Mustard Oil (Packed)", "price_inr_per_kg": 201.42, "category": "Edible Oils", "unit": "₹ / Kg"},
        {"commodity": "Groundnut Oil (Packed)", "price_inr_per_kg": 206.84, "category": "Edible Oils", "unit": "₹ / Kg"},
        {"commodity": "Sunflower Oil (Packed)", "price_inr_per_kg": 193.56, "category": "Edible Oils", "unit": "₹ / Kg"},
        {"commodity": "Potato", "price_inr_per_kg": 23.12, "category": "Vegetables", "unit": "₹ / Kg"},
        {"commodity": "Onion", "price_inr_per_kg": 54.22, "category": "Vegetables", "unit": "₹ / Kg"},
        {"commodity": "Tomato", "price_inr_per_kg": 39.04, "category": "Vegetables", "unit": "₹ / Kg"},
        {"commodity": "Sugar", "price_inr_per_kg": 58.24, "category": "Daily Essentials", "unit": "₹ / Kg"},
        {"commodity": "Milk @", "price_inr_per_kg": 61.40, "category": "Daily Essentials", "unit": "₹ / Kg"},
        {"commodity": "Tea Loose", "price_inr_per_kg": 274.08, "category": "Daily Essentials", "unit": "₹ / Kg"},
        {"commodity": "Salt Pack (Iodised)", "price_inr_per_kg": 22.09, "category": "Daily Essentials", "unit": "₹ / Kg"},
    ]

    fallback = {
        "status": "fallback",
        "as_on_date": datetime.now().strftime("%d/%m/%Y"),
        "fetched_at": datetime.now().isoformat(),
        "total_commodities": len(default_items),
        "source_url": FCA_URL,
        "commodities": default_items
    }

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(fallback, f, indent=2, ensure_ascii=False)

    return fallback
