from datetime import date
import unittest
from unittest.mock import Mock, patch

import pandas as pd
from backend.api.market_prices import refresh_market_prices
from backend.schemas.market_price import MarketPriceRefreshRequest
from backend.services.market_prices import MandiClient, MandiUpstreamTimeout, MarketDataError, build_market_features, infer_controlled_mapping, normalize_mandi_response


class MarketPriceTests(unittest.TestCase):
    def test_normalizes_documented_mandi_record(self):
        records = normalize_mandi_response({"records": [{
        "state": "Karnataka", "district": "Bengaluru", "market": "Binny Mill",
        "commodity": "Onion", "variety": "Other", "arrival_date": "10/07/2022",
        "min_price": "1000", "max_price": "2000", "modal_price": "1500",
        }]})
        self.assertEqual(records[0]["commodity"], "onion")
        self.assertEqual(records[0]["price_date"], date(2022, 7, 10))
        self.assertEqual(records[0]["modal_price"], 1500.0)


    def test_rejects_invalid_or_empty_mandi_responses(self):
        with self.assertRaises(MarketDataError):
            normalize_mandi_response({})
        self.assertEqual(normalize_mandi_response({"records": []}), [])
        with self.assertRaises(MarketDataError):
            normalize_mandi_response({"records": [{"commodity": "Onion"}]})


    def test_features_are_past_and_current_only_and_classify_spike(self):
        prices = pd.DataFrame({
        "commodity": ["onion"] * 8,
        "price_date": pd.date_range("2022-07-01", periods=8),
        "modal_price": [100, 101, 102, 103, 104, 105, 106, 140],
        })
        baseline = build_market_features(prices, spike_zscore=2)
        changed_future = prices.copy()
        changed_future.loc[7, "modal_price"] = 1000
        without_future = build_market_features(changed_future.iloc[:7], spike_zscore=2)
        pd.testing.assert_series_equal(baseline.loc[:6, "price_change_7d"], without_future["price_change_7d"], check_names=False)
        self.assertTrue(bool(baseline.iloc[-1].price_spike_flag))
        self.assertGreater(baseline.iloc[-1].price_change_pct_7d, 0)


class _Product:
    def __init__(self, name, l0, l1):
        self.product_name, self.l0_category, self.l1_category = name, l0, l1




class MappingTests(unittest.TestCase):
    def test_only_controlled_mappings_are_inferred(self):
        self.assertEqual(infer_controlled_mapping(_Product("Onion", "Vegetables & Fruits", "Fresh Vegetables"))[0], "onion")
        self.assertIsNone(infer_controlled_mapping(_Product("Potato Chips", "Munchies", "Chips & Crisps")))
        self.assertIsNone(infer_controlled_mapping(_Product("Generic oil", "Dry Fruits, Masala & Oil", "Oil")))


class RefreshEndpointTests(unittest.TestCase):
    @patch("backend.api.market_prices.seed_controlled_mappings", return_value=2)
    @patch("backend.api.market_prices.upsert_observations", return_value=1)
    @patch.object(MandiClient, "fetch", return_value=[{"commodity": "onion"}])
    def test_successful_refresh_keeps_success_response(self, fetch, upsert, seed):
        response = refresh_market_prices(MarketPriceRefreshRequest(), Mock())
        self.assertEqual(response.fetched, 1)
        self.assertEqual(response.inserted, 1)
        self.assertEqual(response.mappings_created, 2)
        self.assertFalse(response.reforecast_triggered)
        upsert.assert_called_once()
        seed.assert_called_once()

    @patch("backend.api.market_prices.seed_controlled_mappings")
    @patch("backend.api.market_prices.upsert_observations")
    @patch.object(MandiClient, "fetch", side_effect=MandiUpstreamTimeout("timed out"))
    def test_timeout_returns_safe_response_without_database_mutation(self, fetch, upsert, seed):
        response = refresh_market_prices(MarketPriceRefreshRequest(), Mock())
        self.assertEqual(response.status_code, 503)
        self.assertIn(b'"error_code":"upstream_timeout"', response.body)
        self.assertIn(b'"data_changed":false', response.body)
        self.assertIn(b'no market-price data was changed', response.body)
        upsert.assert_not_called()
        seed.assert_not_called()
