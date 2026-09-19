# ML Anomaly & Outlier Detection Engine Report

## Objective
The goal of this engine is to identify and classify statistical anomalies and outliers in daily product demand compared to historical patterns and forecasting models.

## Data Sources
- **Actual Demand Data**: `dataset/processed/daily_product_demand.csv`
- **Forecast Results**: `reports/forecast_results.csv`

## Data Columns Actually Used
- **From actual demand**: `date_`, `product_id`, `city_name`, `daily_quantity` (aliased as `actual_demand`)
- **From forecast results**: `date_`, `product_id`, `city_name`, `pred_hist_gbt` (or fallback, aliased as `expected_demand`)

## Preprocessing
- Loaded 1,764,981 rows from actual demand and 10,000 rows from forecast results.
- Used DuckDB to inner-join actual demand and forecast results on `date_`, `product_id`, and `city_name`.
- Computed a backward-looking 14-day rolling window for baseline statistics (mean, standard deviation).
- Engineered features including `residual`, `relative_residual`, `rolling_volatility` (from rolling standard deviation), and `sales_volume`.

## Rolling Z-Score Methodology
- **Window**: 14 days (backward-looking, excluding current day).
- **Threshold**: Absolute Z-Score `|Z| > 2.5`.
- **Handling Zero Variance**: If the rolling standard deviation is zero but a sudden jump or drop occurs, a proportional score is calculated.

## Isolation Forest Methodology
- **Features Used**: `residual`, `rolling_volatility`, `sales_volume`.
- **Parameters**: `contamination=0.03`, `random_state=42`, `n_estimators=100`.
- Outputs a binary classification (anomaly vs. inlier) and normalizes the decision function score to a 0.0-1.0 scale (`anomaly_score`).

## Anomaly Classification Logic
Anomalies detected by either method are classified as:
- **SPIKE_DEMAND**: Actual demand is significantly above historical mean (positive residual or Z-score).
- **DROP_STOCKOUT**: Actual demand is significantly below historical mean (negative residual or Z-score).
- **PRICE_ANOMALY**: Reserved for explicitly supplied price time-series data. (Not triggered here as price data is unavailable).

## Severity Logic
- **CRITICAL**: `|Z| >= 4.0`, or dual algorithm agreement with `|residual| >= 100` and `|Z| >= 3.0`, or actual <= 10 when expected >= 150 (severe stockout), or residual >= 300 and `|Z| >= 3.5` (massive spike).
- **MEDIUM**: `|Z| >= 2.8`, or Isolation Forest flag with `|residual| >= 75`, or actual < 30% of expected when expected >= 100.
- **LOW**: All other flagged anomalies falling outside Medium or Critical criteria.

## Processing Summary & Results
- **Records processed from Demand**: 1,764,981
- **Records processed from Forecast**: 10,000
- **Matched Records (Evaluation Split)**: 9,662
- **Total Anomalies Detected**: 1,252

### Anomalies by Type
- **SPIKE_DEMAND**: 885
- **DROP_STOCKOUT**: 367
- **PRICE_ANOMALY**: 0

### Anomalies by Severity
- **CRITICAL**: 263
- **MEDIUM**: 712
- **LOW**: 277

## Output File
- **Location**: `reports/demand_anomalies.csv`
- Schema includes `date_`, `product_id`, `city_name`, `actual_demand`, `expected_demand`, `anomaly_score`, `anomaly_type`, `severity`, and `action_recommendation`.

## API Endpoint
- **Endpoint**: `GET /api/v1/analytics/anomalies`
- Returns the active anomaly alerts filtered by severity (defaults to CRITICAL), city, or product ID. Returns JSON containing `count` and `alerts` matching the exact schema above.

## Testing Performed
- Ran the `anomaly_detection_engine.py` script.
- Verified successful DuckDB processing and ML model fitting.
- Verified `reports/demand_anomalies.csv` output generation and counts.
- Tested the FastAPI endpoint by instantiating the router via `TestClient` to ensure valid JSON responses adhering to the required schema.

## Limitations
> [!IMPORTANT]
> **Operational Interpretation Caveat**: An anomaly does not prove its operational cause. For example, a demand drop may indicate a potential stockout/supply issue but must not be presented as confirmed without supporting data (like real-time inventory counts).
- Cold start items with fewer than 7 days of history cannot have reliable Z-Scores computed.
- The Isolation Forest algorithm depends on the random state; while fixed here (42) for determinism, model updates may alter definitions of an anomaly.
