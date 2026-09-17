from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.market_price import MarketPriceRefreshRequest, MarketPriceSummary, RefreshResponse
from backend.services.market_prices import (
    MandiClient, MandiResponseValidationError, MandiUpstreamError,
    MandiUpstreamTimeout, latest_market_summary, seed_controlled_mappings,
    upsert_observations,
)

router = APIRouter()


@router.get("/latest", response_model=list[MarketPriceSummary], summary="Get latest market-price feature for each commodity")
def get_latest_market_prices(commodity: str | None = Query(None, max_length=200), db: Session = Depends(get_db)):
    return latest_market_summary(db, commodity)


@router.get("/trend", response_model=list[MarketPriceSummary], summary="Get leakage-safe market trend features")
def get_market_trend(commodity: str | None = Query(None, max_length=200), db: Session = Depends(get_db)):
    return latest_market_summary(db, commodity)


@router.post("/refresh", response_model=RefreshResponse, summary="Fetch and store current Mandi observations")
def refresh_market_prices(request: MarketPriceRefreshRequest, db: Session = Depends(get_db)):
    try:
        observations = MandiClient().fetch(commodity=request.commodity, state=request.state)
        inserted = upsert_observations(db, observations)
        mappings_created = seed_controlled_mappings(db) if request.seed_product_mappings else 0
    except MandiUpstreamTimeout:
        return JSONResponse(status_code=503, content={
            "status": "failed", "source": "mandi", "error_code": "upstream_timeout",
            "message": "Mandi upstream request timed out; no market-price data was changed.",
            "fetched": 0, "inserted": 0, "mappings_created": 0,
            "reforecast_triggered": False, "data_changed": False,
        })
    except MandiUpstreamError:
        return JSONResponse(status_code=502, content={
            "status": "failed", "source": "mandi", "error_code": "upstream_failure",
            "message": "Mandi upstream request failed; no market-price data was changed.",
            "fetched": 0, "inserted": 0, "mappings_created": 0,
            "reforecast_triggered": False, "data_changed": False,
        })
    except MandiResponseValidationError as exc:
        # The source responded, but its payload cannot be safely ingested.
        raise HTTPException(status_code=502, detail="Mandi response validation failed; no market-price data was changed.") from exc
    return RefreshResponse(
        fetched=len(observations), inserted=inserted, mappings_created=mappings_created,
        detail="Observations stored. Reforecasting is intentionally not triggered until overlapping historical market data is available."
    )


@router.post("/reforecast", status_code=409, summary="Explain market-aware reforecast eligibility")
def reforecast_market_aware():
    """A guarded endpoint: it never creates unsupported forecast versions or fabricated forecasts."""
    raise HTTPException(
        status_code=409,
        detail="Market-aware reforecast requires a validated, overlapping historical price series and a completed evaluation. No production reforecast has been enabled yet.",
    )
