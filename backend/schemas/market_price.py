from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class MarketPriceRefreshRequest(BaseModel):
    commodity: Optional[str] = Field(None, max_length=200)
    state: Optional[str] = Field(None, max_length=100)
    seed_product_mappings: bool = True


class MarketPriceSummary(BaseModel):
    commodity: str
    price_date: date
    market_price: float
    price_change_1d: Optional[float] = None
    price_change_pct_7d: Optional[float] = None
    price_volatility_7d: Optional[float] = None
    price_trend_direction: str
    price_spike_flag: bool


class RefreshResponse(BaseModel):
    fetched: int
    inserted: int
    mappings_created: int
    reforecast_triggered: bool = False
    detail: str
