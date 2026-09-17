"""Mandi ingestion, leakage-safe market features, and controlled mappings."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable
import json

import numpy as np
import pandas as pd
import requests
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.market_price import MarketPriceObservation, ProductCommodityMapping
from backend.models.product import Product

MANDI_SOURCE = "mandi"


class MarketDataError(ValueError):
    """An external source returned a response which cannot be safely ingested."""


class MandiUpstreamError(MarketDataError):
    """The Mandi gateway could not provide a response."""


class MandiUpstreamTimeout(MandiUpstreamError):
    """The Mandi gateway did not respond before the client timeout."""


class MandiResponseValidationError(MarketDataError):
    """Mandi responded, but the payload cannot be safely normalized."""


def _field(record: dict[str, Any], *names: str) -> Any:
    normalized = {str(k).strip().lower().replace(" ", "_"): v for k, v in record.items()}
    for name in names:
        value = normalized.get(name)
        if value not in (None, "", "NA", "N/A"):
            return value
    return None


def _number(value: Any) -> float | None:
    if value in (None, "", "NA", "N/A"):
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError) as exc:
        raise MandiResponseValidationError(f"Invalid price value: {value!r}") from exc


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise MandiResponseValidationError(f"Invalid price date: {value!r}")
    return parsed.date()


def normalize_mandi_response(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize the documented data.gov.in records envelope without guessing fields."""
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise MandiResponseValidationError("Mandi response must be an object with a records list")
    observations: list[dict[str, Any]] = []
    for record in payload["records"]:
        if not isinstance(record, dict):
            raise MandiResponseValidationError("Mandi records must be objects")
        commodity = _field(record, "commodity")
        price_date = _field(record, "arrival_date", "price_date", "date")
        if not commodity or not price_date:
            raise MandiResponseValidationError("Mandi record is missing commodity or arrival_date")
        min_price = _number(_field(record, "min_price", "min._price"))
        max_price = _number(_field(record, "max_price", "max._price"))
        modal_price = _number(_field(record, "modal_price", "modal._price"))
        if min_price is None and max_price is None and modal_price is None:
            raise MandiResponseValidationError("Mandi record contains no price")
        observations.append({
            "source": MANDI_SOURCE,
            "commodity": str(commodity).strip().lower(),
            "variety": str(_field(record, "variety") or "").strip(),
            "market": str(_field(record, "market") or "").strip(),
            "state": str(_field(record, "state") or "").strip(),
            "district": str(_field(record, "district") or "").strip(),
            "price_date": _parse_date(price_date),
            "min_price": min_price,
            "max_price": max_price,
            "modal_price": modal_price,
            "unit": str(_field(record, "unit") or "INR/quintal").strip(),
            "raw_source_reference": json.dumps(record, sort_keys=True, default=str),
        })
    return observations


class MandiClient:
    def fetch(self, *, commodity: str | None = None, state: str | None = None, limit: int = 1000) -> list[dict[str, Any]]:
        if not settings.MANDI_API_KEY:
            raise MarketDataError("MANDI_API_KEY is not configured")
        headers = {"Authorization": settings.MANDI_API_KEY}
        params: dict[str, Any] = {"format": "json", "limit": limit}
        if commodity:
            params["filters[commodity]"] = commodity
        if state:
            params["filters[state]"] = state
        url = f"{settings.MANDI_API_BASE_URL.rstrip('/')}/{settings.MANDI_RESOURCE_ID}"
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            payload = response.json()
        except requests.Timeout as exc:
            raise MandiUpstreamTimeout("Mandi upstream request timed out") from exc
        except requests.RequestException as exc:
            raise MandiUpstreamError("Mandi upstream request failed") from exc
        except ValueError as exc:
            raise MandiResponseValidationError("Mandi returned invalid JSON") from exc
        return normalize_mandi_response(payload)


def upsert_observations(db: Session, observations: Iterable[dict[str, Any]]) -> int:
    rows = list(observations)
    if not rows:
        return 0
    stmt = insert(MarketPriceObservation).values(rows)
    stmt = stmt.on_conflict_do_nothing(constraint="uq_market_price_observation")
    result = db.execute(stmt)
    db.commit()
    return result.rowcount or 0


# Only exact, independently meaningful product/category evidence is used.  No fuzzy matching.
CONTROLLED_MAPPING_RULES = (
    ("exact_fresh_vegetable_name", "onion", "onion", "Vegetables & Fruits / Fresh Vegetables and exact product name Onion"),
    ("exact_fresh_vegetable_name", "tomato", "tomato", "Vegetables & Fruits / Fresh Vegetables and exact product name Tomato"),
    ("exact_fresh_vegetable_name", "potato", "potato", "Vegetables & Fruits / Fresh Vegetables and exact product name Potato"),
    ("rice_category", None, "rice", "Atta, Rice & Dal / Rice category"),
)


def infer_controlled_mapping(product: Product) -> tuple[str, str] | None:
    name = (product.product_name or "").strip().casefold()
    l0 = (product.l0_category or "").strip().casefold()
    l1 = (product.l1_category or "").strip().casefold()
    if l0 == "vegetables & fruits" and l1 == "fresh vegetables" and name in {"onion", "tomato", "potato"}:
        return name, "Exact fresh-vegetable product name with matching Fresh Vegetables category"
    if l0 == "atta, rice & dal" and l1 == "rice":
        return "rice", "Explicit Rice product category; not inferred from product-name tokens"
    return None


def seed_controlled_mappings(db: Session) -> int:
    created = 0
    for product in db.query(Product).yield_per(1000):
        candidate = infer_controlled_mapping(product)
        if candidate and not product.commodity_mapping:
            commodity, reason = candidate
            db.add(ProductCommodityMapping(product_id=product.product_id, commodity=commodity, mapping_reason=reason))
            created += 1
    db.commit()
    return created


def build_market_features(prices: pd.DataFrame, *, spike_zscore: float | None = None, trend_volatility_multiplier: float | None = None) -> pd.DataFrame:
    """Build past/current-only features. Each row uses observations at or before its date."""
    required = {"commodity", "price_date"}
    if not required.issubset(prices.columns):
        raise ValueError("prices must contain commodity and price_date")
    available_price_columns = [c for c in ("modal_price", "wholesale_price", "retail_price") if c in prices.columns]
    if not available_price_columns:
        raise ValueError("prices must contain modal_price, wholesale_price, or retail_price")
    frame = prices[["commodity", "price_date", *available_price_columns]].copy()
    frame["price_date"] = pd.to_datetime(frame["price_date"])
    # Prefer modal wholesale price, then an explicitly sourced wholesale/retail
    # price. This is row-wise so future FCA observations remain usable.
    frame["market_price"] = frame[available_price_columns].apply(pd.to_numeric, errors="coerce").bfill(axis=1).iloc[:, 0]
    frame = frame.dropna(subset=["market_price"]).groupby(["commodity", "price_date"], as_index=False)["market_price"].mean()
    frame = frame.sort_values(["commodity", "price_date"]).reset_index(drop=True)
    group = frame.groupby("commodity", group_keys=False)["market_price"]
    for days in (1, 7, 14, 30):
        frame[f"price_change_{days}d"] = group.diff(days)
        frame[f"price_change_pct_{days}d"] = group.pct_change(days, fill_method=None) * 100
    frame["price_volatility_7d"] = group.transform(lambda s: s.rolling(7, min_periods=2).std(ddof=0))
    frame["price_volatility_30d"] = group.transform(lambda s: s.rolling(30, min_periods=2).std(ddof=0))
    multiplier = settings.MARKET_TREND_VOLATILITY_MULTIPLIER if trend_volatility_multiplier is None else trend_volatility_multiplier
    threshold = frame["price_volatility_7d"].fillna(np.inf) * multiplier
    frame["price_trend_direction"] = np.select(
        [frame["price_change_7d"] > threshold, frame["price_change_7d"] < -threshold],
        ["increasing", "decreasing"], default="stable"
    )
    zscore = settings.MARKET_SPIKE_ZSCORE if spike_zscore is None else spike_zscore
    frame["price_spike_flag"] = (frame["price_change_1d"].abs() > zscore * frame["price_volatility_7d"]).fillna(False)
    return frame


def latest_market_summary(db: Session, commodity: str | None = None) -> list[dict[str, Any]]:
    query = db.query(MarketPriceObservation)
    if commodity:
        query = query.filter(MarketPriceObservation.commodity == commodity.casefold())
    rows = query.order_by(MarketPriceObservation.commodity, MarketPriceObservation.price_date).all()
    if not rows:
        return []
    features = build_market_features(pd.DataFrame([{
        "commodity": r.commodity, "price_date": r.price_date, "modal_price": r.modal_price,
        "wholesale_price": r.wholesale_price, "retail_price": r.retail_price,
    } for r in rows]))
    latest = features.groupby("commodity", as_index=False).tail(1)
    return latest.replace({np.nan: None}).to_dict(orient="records")
