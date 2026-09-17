# Market-price backend

## Scope and architecture

`market_price_observations` stores immutable, source-labelled price observations. Mandi observations retain their minimum, maximum, and modal wholesale prices. FCA retail and wholesale values have separate columns for a future official adapter. `product_commodity_mappings` is an explicit, one-product-to-one-commodity mapping table; it is never populated by fuzzy matching.

The intended flow is Mandi refresh -> duplicate-safe storage -> market trend features -> validated market-aware evaluation -> new `forecast_runs` version -> existing inventory calculation. Existing forecasts and inventory records are never overwritten.

## Sources

Mandi is the active adapter. It calls the official data.gov.in resource endpoint configured by `MANDI_API_BASE_URL` and `MANDI_RESOURCE_ID`, with `MANDI_API_KEY` read only from `backend/.env`. The normalizer accepts the documented `records` envelope and fields including `state`, `district`, `market`, `commodity`, `variety`, `arrival_date`, `min_price`, `max_price`, and `modal_price`. API keys are not logged or returned.

FCAInfoWeb is an official source with published daily-price information, but no stable, documented machine-readable API was verified. No scraper is implemented. A future adapter may write its explicitly labelled retail/wholesale observations into the same table.

Example `backend/.env` values (use a real key locally; do not commit the file):

```dotenv
MANDI_API_KEY=your_data_gov_in_key
# Override only after verifying a changed official resource ID.
# MANDI_RESOURCE_ID=9ef84268-d588-465a-a308-a864a43d0070
```

## Mappings

The controlled mapper maps only: exact `Onion`, `Tomato`, and `Potato` products in `Vegetables & Fruits / Fresh Vegetables`; and products in `Atta, Rice & Dal / Rice` to `rice`. Packaged products, oil products, ambiguous names, and all unmatched products remain unmapped. Mapping reasons are stored with each mapping.

## Features and leakage prevention

`build_market_features` aggregates same-commodity observations by date and calculates current/past-only 1/7/14/30-day changes, percentage changes, 7/30-day volatility, trend, and spike flag. At date T every value uses records dated T or earlier. Trend is `increasing`/`decreasing` only when the 7-day change exceeds the configurable 7-day standard deviation multiplier; otherwise it is `stable`. Spike uses the configurable three-standard-deviation rule (`MARKET_SPIKE_ZSCORE=3.0`). Neither setting is tuned to improve results.

`forecasting/market_aware.py` offers a comparable chronological Ridge evaluation: sales-only versus sales-plus-market on the same rows and split. It rejects missing market history rather than inventing or forward-filling observations. The short 2022 sales period currently has no ingested, verified overlapping Mandi history, so no market-aware result has been run and no claim of improvement is made.

## APIs and reforecasting

* `GET /api/market-prices/latest?commodity=` returns the latest computed feature per commodity.
* `GET /api/market-prices/trend?commodity=` returns the same leakage-safe trend view.
* `POST /api/market-prices/refresh` fetches Mandi, upserts duplicates, and optionally applies controlled mappings.
* `POST /api/market-prices/reforecast` is deliberately guarded with `409` until an overlapping series and evaluation exist. It does not create a misleading forecast run or fabricated inventory recommendation.

When eligibility exists, reforecasting must create a new `forecast_runs` record and new forecast/inventory recommendation records rather than overwriting old versions. Price alone must never make an inventory decision; only a validated updated demand forecast may feed the existing inventory logic.

## Commands

```powershell
python -m backend.db.init_db
python -m pytest tests/test_market_prices.py
uvicorn backend.main:app --reload
```
