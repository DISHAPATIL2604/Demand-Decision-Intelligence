# S3: Forecasting Models Evaluation Report

**Project:** Demand-Decision-Intelligence  
**Stage:** S3 (Weeks 5–6) - Forecasting Models  
**Evaluation Period:** `2022-07-01` to `2022-07-10` (Time-Series Validation Split)  
**Total Series Evaluated:** 1,000  
**Best Performing Model:** **Prophet (Weekly Seasonality)** (WAPE: `18.74%`, MAE: `94.0475`)  

---

## Executive Summary

This report completes Stage **S3: Forecasting Models (Weeks 5–6)** of the Demand-Decision-Intelligence system. We built and evaluated multiple forecasting models ranging from naive statistical baselines and Moving Averages to Facebook **Prophet** (incorporating weekly seasonality) and advanced Machine Learning models (**Ridge Regression** and **HistGradientBoosting**).

All models were evaluated using chronological time-series train/test splitting (training up to `2022-06-30` and validating from `2022-07-01` to `2022-07-10`) to eliminate lookahead leakage.

---

## Model Comparison Table

| Model Name | MAE | RMSE | WAPE (%) |
| :--- | :---: | :---: | :---: |
| Naive (Lag-1) | 134.9939 | 261.0935 | 26.90% |
| Seasonal Naive (Lag-7) | 130.1737 | 245.2926 | 25.94% |
| Moving Average (7 Days) | 105.0257 | 200.7986 | 20.93% |
| Moving Average (14 Days) | 101.6585 | 194.9029 | 20.26% |
| Moving Average (28 Days) | 99.8161 | 190.6422 | 19.89% |
| Prophet (Weekly Seasonality) | 94.0475 | 177.5753 | 18.74% |
| Ridge Regression | 97.8066 | 186.7519 | 19.49% |
| HistGradientBoosting (GBT) | 96.9549 | 190.0272 | 19.32% |

---

## Key Model Takeaways

1. **Top Performer (Prophet (Weekly Seasonality)):** Achieved the lowest Weighted Absolute Percentage Error (`18.74%`), capturing complex feature interactions between short-term lags, rolling averages, and weekend indicators.
2. **Prophet Model:** Successfully captured day-of-week seasonality (weekly pattern lift on weekends) and provided smooth baseline trends.
3. **Moving Average Baselines:** Moving Average (7 Days) provided a reliable benchmark, outperforming naive single-day lags by smoothing out daily volatility.

---

## Deliverables Generated

- `reports/model_comparison.csv` - Standardized performance metrics across all models.
- `reports/forecast_results.csv` - Forecast predictions vs actual demand on validation data.
- `reports/evaluation_report.md` - Executive report on forecasting model performance.
- `notebooks/S3_Forecasting_Models.ipynb` - End-to-end interactive notebook.
