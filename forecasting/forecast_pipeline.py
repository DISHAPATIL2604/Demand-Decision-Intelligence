import time
import json
import duckdb
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

project_root = Path(__file__).resolve().parent.parent
demand_file = project_root / "dataset" / "processed" / "daily_product_demand.csv"
reports_dir = project_root / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

print("=" * 75)
print("DEMAND DECISION INTELLIGENCE: FORECASTING PIPELINE (PHASES 6, 7 & 8)")
print("=" * 75)

t_start = time.time()
con = duckdb.connect()

# =====================================================================
# PHASE 6: FEATURE ENGINEERING VIA COMPLETE PRODUCT-CITY CALENDAR
# =====================================================================
print("\n[PHASE 6] Building complete calendar & feature engineering via DuckDB...")

feature_query = f"""
WITH raw_demand AS (
    SELECT 
        CAST(date_ AS DATE) AS date_,
        product_id,
        city_name,
        daily_quantity
    FROM read_csv_auto('{demand_file.as_posix()}')
),
distinct_series AS (
    SELECT DISTINCT product_id, city_name
    FROM raw_demand
),
calendar_dates AS (
    SELECT CAST(d AS DATE) AS date_
    FROM generate_series(DATE '2022-04-01', DATE '2022-07-10', INTERVAL 1 DAY) t(d)
),
complete_grid AS (
    SELECT 
        c.date_,
        s.product_id,
        s.city_name,
        COALESCE(r.daily_quantity, 0.0) AS daily_quantity
    FROM distinct_series s
    CROSS JOIN calendar_dates c
    LEFT JOIN raw_demand r 
        ON s.product_id = r.product_id 
       AND s.city_name = r.city_name 
       AND c.date_ = r.date_
),
features AS (
    SELECT 
        date_,
        product_id,
        city_name,
        daily_quantity,
        -- Lags (backward-looking only)
        LAG(daily_quantity, 1) OVER w AS lag_1,
        LAG(daily_quantity, 7) OVER w AS lag_7,
        LAG(daily_quantity, 14) OVER w AS lag_14,
        LAG(daily_quantity, 28) OVER w AS lag_28,
        -- Rolling statistics over past windows (ROWS BETWEEN N PRECEDING AND 1 PRECEDING)
        -- Strictly avoids lookahead leakage!
        AVG(daily_quantity) OVER (w ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS rolling_mean_7,
        AVG(daily_quantity) OVER (w ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_mean_14,
        AVG(daily_quantity) OVER (w ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS rolling_mean_28,
        STDDEV(daily_quantity) OVER (w ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS rolling_std_7,
        -- Calendar features
        DAYOFWEEK(date_) - 1 AS day_of_week, -- 0=Monday .. 6=Sunday
        CASE WHEN DAYOFWEEK(date_) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend
    FROM complete_grid
    WINDOW w AS (PARTITION BY product_id, city_name ORDER BY date_)
)
SELECT * 
FROM features
WHERE lag_28 IS NOT NULL 
  AND rolling_mean_28 IS NOT NULL
ORDER BY product_id, city_name, date_
"""

print("Executing SQL feature transformation...")
t_feat = time.time()
df_features = con.execute(feature_query).df()
print(f"Features generated in {time.time() - t_feat:.2f}s!")

total_feature_rows = len(df_features)
min_date = df_features["date_"].min()
max_date = df_features["date_"].max()
unique_series = df_features.groupby(["product_id", "city_name"]).ngroups

print(f"\nFeature Table Summary:")
print(f"Total model rows : {total_feature_rows:,} (Expected: 3,380,265)")
print(f"Unique series    : {unique_series:,} (Expected: 46,305)")
print(f"Date range       : {min_date} to {max_date}")

# Validation of feature non-nullness
feature_cols = [
    "lag_1", "lag_7", "lag_14", "lag_28",
    "rolling_mean_7", "rolling_mean_14", "rolling_mean_28", "rolling_std_7",
    "day_of_week", "is_weekend"
]
# For the first 7 days of rolling window, rolling_std_7 might have null if stddev needs >1 sample, fillna with 0
df_features["rolling_std_7"] = df_features["rolling_std_7"].fillna(0.0)

null_counts = df_features[feature_cols].isna().sum()
print("\nFeature Null Counts (must be 0):")
print(null_counts)
assert null_counts.sum() == 0, "Error: Features contain null values!"

# Train / Validation Split
df_features["date_"] = pd.to_datetime(df_features["date_"])
split_date = pd.Timestamp("2022-07-01")
train_mask = df_features["date_"] < split_date
val_mask = df_features["date_"] >= split_date

train_df = df_features[train_mask]
val_df = df_features[val_mask]

print(f"\nTemporal Split:")
print(f"Train rows       : {len(train_df):,} ({train_df['date_'].min()} to {train_df['date_'].max()})")
print(f"Validation rows  : {len(val_df):,} ({val_df['date_'].min()} to {val_df['date_'].max()})")

X_train = train_df[feature_cols].values
y_train = train_df["daily_quantity"].values
X_val = val_df[feature_cols].values
y_val = val_df["daily_quantity"].values

# =====================================================================
# PHASE 7: FORECASTING BASELINES & ML MODELS
# =====================================================================
print("\n" + "=" * 75)
print("[PHASE 7] Evaluating Forecasting Models")
print("=" * 75)

def evaluate_predictions(y_true, y_pred, model_name):
    y_pred_clipped = np.clip(y_pred, 0, None) # demand is non-negative
    mae = mean_absolute_error(y_true, y_pred_clipped)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred_clipped))
    total_actual = np.sum(y_true)
    wape = (np.sum(np.abs(y_true - y_pred_clipped)) / total_actual) * 100 if total_actual > 0 else 0.0
    return {
        "model": model_name,
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "WAPE_pct": round(float(wape), 2)
    }

results = []

# Baseline 1: Naive Lag-1
val_pred_lag1 = val_df["lag_1"].values
res_lag1 = evaluate_predictions(y_val, val_pred_lag1, "Naive (Lag-1)")
results.append(res_lag1)
print(f"1. Naive Lag-1        -> MAE: {res_lag1['MAE']:.4f}, RMSE: {res_lag1['RMSE']:.4f}, WAPE: {res_lag1['WAPE_pct']:.2f}%")

# Baseline 2: Seasonal Naive Lag-7
val_pred_lag7 = val_df["lag_7"].values
res_lag7 = evaluate_predictions(y_val, val_pred_lag7, "Seasonal Naive (Lag-7)")
results.append(res_lag7)
print(f"2. Seasonal Naive L-7 -> MAE: {res_lag7['MAE']:.4f}, RMSE: {res_lag7['RMSE']:.4f}, WAPE: {res_lag7['WAPE_pct']:.2f}%")

# Baseline 3: Rolling Mean 7
val_pred_rm7 = val_df["rolling_mean_7"].values
res_rm7 = evaluate_predictions(y_val, val_pred_rm7, "Rolling Mean 7")
results.append(res_rm7)
print(f"3. Rolling Mean 7     -> MAE: {res_rm7['MAE']:.4f}, RMSE: {res_rm7['RMSE']:.4f}, WAPE: {res_rm7['WAPE_pct']:.2f}%")

# ML Model 1: Ridge Regression
print("\nTraining Ridge Regression on full dataset...")
t_ridge = time.time()
ridge = Ridge(alpha=1.0)
ridge.fit(X_train, y_train)
val_pred_ridge = ridge.predict(X_val)
res_ridge = evaluate_predictions(y_val, val_pred_ridge, "Ridge Regression")
results.append(res_ridge)
print(f"4. Ridge Regression   -> MAE: {res_ridge['MAE']:.4f}, RMSE: {res_ridge['RMSE']:.4f}, WAPE: {res_ridge['WAPE_pct']:.2f}% (Trained in {time.time() - t_ridge:.2f}s)")

# ML Model 2: HistGradientBoostingRegressor (Subsampled train for speed & efficiency)
print("\nTraining HistGradientBoostingRegressor (Gradient Boosted Trees)...")
t_gbt = time.time()
# Train on 300,000 recent samples to ensure fast training and focus on latest dynamics
np.random.seed(42)
sample_idx = np.random.choice(len(train_df), size=min(300_000, len(train_df)), replace=False)
hgbt = HistGradientBoostingRegressor(max_iter=60, min_samples_leaf=50, random_state=42)
hgbt.fit(X_train[sample_idx], y_train[sample_idx])
val_pred_gbt = hgbt.predict(X_val)
res_gbt = evaluate_predictions(y_val, val_pred_gbt, "HistGradientBoosting (GBT)")
results.append(res_gbt)
print(f"5. HistGradientBoost  -> MAE: {res_gbt['MAE']:.4f}, RMSE: {res_gbt['RMSE']:.4f}, WAPE: {res_gbt['WAPE_pct']:.2f}% (Trained in {time.time() - t_gbt:.2f}s)")

df_results = pd.DataFrame(results)
print("\nModel Comparison Table:")
print(df_results.to_string(index=False))

# Best model selection
best_model_name = df_results.sort_values(by="WAPE_pct").iloc[0]["model"]
print(f"\n>>> Best Performing Model: {best_model_name} <<<")

# =====================================================================
# PHASE 8: COMPREHENSIVE ERROR ANALYSIS
# =====================================================================
print("\n" + "=" * 75)
print("[PHASE 8] Detailed Error Analysis (HistGradientBoosting / Best Model)")
print("=" * 75)

val_eval_df = val_df.copy()
val_eval_df["y_pred"] = np.clip(val_pred_gbt, 0, None)
val_eval_df["abs_error"] = np.abs(val_eval_df["daily_quantity"] - val_eval_df["y_pred"])
val_eval_df["squared_error"] = (val_eval_df["daily_quantity"] - val_eval_df["y_pred"]) ** 2

# 1. Error by City
city_error = val_eval_df.groupby("city_name").agg(
    total_actual=("daily_quantity", "sum"),
    total_pred=("y_pred", "sum"),
    mae=("abs_error", "mean"),
    total_abs_error=("abs_error", "sum")
).reset_index()
city_error["wape_pct"] = (city_error["total_abs_error"] / city_error["total_actual"]) * 100
city_error["wape_pct"] = city_error["wape_pct"].round(2)
city_error["mae"] = city_error["mae"].round(4)
print("\n1. Error Breakdown by City:")
print(city_error[["city_name", "total_actual", "total_pred", "mae", "wape_pct"]].to_string(index=False))

# 2. Error by Demand Sparsity / Intermittency
# High intermittency: product-cities with zero demand for >= 70% of validation days
series_zero_ratio = val_eval_df.groupby(["product_id", "city_name"]).agg(
    zero_days=("daily_quantity", lambda x: (x == 0).sum()),
    total_days=("daily_quantity", "count"),
    total_actual=("daily_quantity", "sum"),
    total_abs_error=("abs_error", "sum")
).reset_index()
series_zero_ratio["zero_pct"] = series_zero_ratio["zero_days"] / series_zero_ratio["total_days"]
series_zero_ratio["demand_type"] = np.where(series_zero_ratio["zero_pct"] >= 0.7, "Sparse / Intermittent", "Regular / Frequent")

sparsity_summary = series_zero_ratio.groupby("demand_type").agg(
    series_count=("product_id", "count"),
    total_actual=("total_actual", "sum"),
    total_abs_error=("total_abs_error", "sum")
).reset_index()
sparsity_summary["wape_pct"] = ((sparsity_summary["total_abs_error"] / sparsity_summary["total_actual"]) * 100).round(2)
print("\n2. Error Breakdown by Demand Intermittency:")
print(sparsity_summary.to_string(index=False))

# 3. Top 10 Product Series with Highest Absolute Forecast Error
top_error_series = val_eval_df.groupby(["product_id", "city_name"]).agg(
    total_actual=("daily_quantity", "sum"),
    total_pred=("y_pred", "sum"),
    total_abs_error=("abs_error", "sum"),
    mae=("abs_error", "mean")
).reset_index().sort_values(by="total_abs_error", ascending=False).head(10)

print("\n3. Top 10 High-Error Product-City Series in Validation Period:")
print(top_error_series.to_string(index=False))

# Save all metrics to reports
report_payload = {
    "feature_rows": int(total_feature_rows),
    "train_rows": int(len(train_df)),
    "validation_rows": int(len(val_df)),
    "train_period": [str(train_df['date_'].min()), str(train_df['date_'].max())],
    "val_period": [str(val_df['date_'].min()), str(val_df['date_'].max())],
    "models_evaluated": results,
    "best_model": best_model_name,
    "city_breakdown": city_error.to_dict(orient="records"),
    "sparsity_breakdown": sparsity_summary.to_dict(orient="records"),
    "top_error_series": top_error_series.to_dict(orient="records")
}

with open(reports_dir / "forecast_evaluation_report.json", "w") as f:
    json.dump(report_payload, f, indent=2)

print(f"\nFull evaluation report saved to: {reports_dir / 'forecast_evaluation_report.json'}")
print(f"Total pipeline execution time: {time.time() - t_start:.2f}s")
print("=" * 75)
con.close()
