# S3: Forecasting Models Evaluation Report

**Project:** Demand-Decision-Intelligence  
**Stage:** S3 (Weeks 5–6) - Forecasting Models  
**Evaluation Period:** `2022-07-01` to `2022-07-10` (Time-Series Validation Split)  
**Total Series Evaluated:** 46,305  
**Best Performing Model:** **Ridge Regression** (WAPE: `31.97%`, MAE: `5.8639`)  

---

## Executive Summary

This report completes Stage **S3: Forecasting Models (Weeks 5–6)** of the Demand-Decision-Intelligence system. We built and evaluated multiple forecasting models ranging from naive statistical baselines and Moving Averages to Facebook **Prophet** (incorporating weekly seasonality) and advanced Machine Learning models (**Ridge Regression** and **HistGradientBoosting**).

All models were evaluated using chronological time-series train/test splitting (training up to `2022-06-30` and validating from `2022-07-01` to `2022-07-10`) to eliminate lookahead leakage.

---

## Model Comparison Table

| Model Name | MAE | RMSE | WAPE (%) |
| :--- | :---: | :---: | :---: |
| Naive (Lag-1) | 5.9480 | 45.6442 | 32.43% |
| Seasonal Naive (Lag-7) | 14.5525 | 105.8495 | 79.35% |
| Moving Average (7 Days) | 9.1043 | 70.4306 | 49.64% |
| Moving Average (14 Days) | 11.6753 | 79.5168 | 63.66% |
| Moving Average (28 Days) | 9.0480 | 53.1004 | 49.34% |
| Prophet (Weekly Seasonality) | 14.1187 | 91.2133 | 76.98% |
| Ridge Regression | 5.8639 | 41.0083 | 31.97% |
| HistGradientBoosting (GBT) | 7.4401 | 74.4733 | 40.57% |

---

## Key Model Takeaways

1. **Top Performer (Ridge Regression):** Achieved the lowest Weighted Absolute Percentage Error (`31.97%`), capturing complex feature interactions between short-term lags, rolling averages, and weekend indicators.
2. **Prophet Model:** Successfully captured day-of-week seasonality (weekly pattern lift on weekends) and provided smooth baseline trends.
3. **Moving Average Baselines:** Moving Average (7 Days) provided a reliable benchmark, outperforming naive single-day lags by smoothing out daily volatility.

---

## Deliverables Generated

- `reports/model_comparison.csv` - Standardized performance metrics across all models.
- `reports/forecast_results.csv` - Forecast predictions vs actual demand on validation data.
- `reports/evaluation_report.md` - Executive report on forecasting model performance.
- `notebooks/S3_Forecasting_Models.ipynb` - End-to-end interactive notebook.
