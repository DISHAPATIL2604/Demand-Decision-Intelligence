"""
Demand Anomaly & Outlier Detection Engine
Project: Demand-Decision-Intelligence
Location: analytics/anomaly_detection_engine.py

Purpose:
Unsupervised Machine Learning and statistical anomaly detection engine combining:
1. Rolling Z-Score (14-day backward window, |Z| > 2.5) for trend/shift detection
2. Isolation Forest (contamination=0.03, random_state=42) for multi-dimensional residual outliers

Classifies anomalies into:
- SPIKE_DEMAND: Actual demand significantly exceeds expected/historical levels
- DROP_STOCKOUT: Actual demand drops sharply below forecast (potential supply/stockout)
- PRICE_ANOMALY: Documented as unavailable unless explicit price time-series is supplied

Assigns deterministic severity levels (CRITICAL, MEDIUM, LOW) and operational action recommendations.
Exports canonical deliverable: reports/demand_anomalies.csv
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Reconfigure stdout/stderr on Windows to avoid charmap encoding errors
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AnomalyDetectionEngine")


class DemandAnomalyDetector:
    """
    Unsupervised ML Anomaly Detection Engine for Retail Demand Forecasting.
    Combines Rolling Z-Score and Scikit-Learn Isolation Forest.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        contamination: float = 0.03,
        z_threshold: float = 2.5,
        rolling_window: int = 14,
        min_history_days: int = 7,
        random_state: int = 42,
        expected_demand_col: str = "pred_hist_gbt"
    ):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.demand_file = self.project_root / "dataset" / "processed" / "daily_product_demand.csv"
        self.forecast_file = self.project_root / "reports" / "forecast_results.csv"
        self.output_csv = self.project_root / "reports" / "demand_anomalies.csv"

        self.contamination = contamination
        self.z_threshold = z_threshold
        self.rolling_window = rolling_window
        self.min_history_days = min_history_days
        self.random_state = random_state
        self.expected_demand_col = expected_demand_col

        # Run statistics container
        self.stats: Dict[str, Any] = {}
        self.iso_model: Optional[IsolationForest] = None

    def load_data(
        self,
        demand_path: Optional[Path] = None,
        forecast_path: Optional[Path] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Loads actual demand and forecast results, validating paths and schema existence.
        """
        d_path = demand_path or self.demand_file
        f_path = forecast_path or self.forecast_file

        if not d_path.exists():
            raise FileNotFoundError(f"Actual demand dataset not found at: {d_path}")
        if not f_path.exists():
            raise FileNotFoundError(f"Forecast results dataset not found at: {f_path}")

        logger.info(f"Loading actual demand data from: {d_path}")
        df_demand = pd.read_csv(d_path)
        logger.info(f"Loaded {len(df_demand):,} rows from actual demand.")

        logger.info(f"Loading expected forecast data from: {f_path} (READ-ONLY)")
        df_forecast = pd.read_csv(f_path)
        logger.info(f"Loaded {len(df_forecast):,} rows from forecast results.")

        # Validate schema presence
        req_demand_cols = {"date_", "product_id", "city_name", "daily_quantity"}
        req_forecast_cols = {"date_", "product_id", "city_name"}

        missing_d = req_demand_cols - set(df_demand.columns)
        if missing_d:
            raise KeyError(f"Missing required columns in actual demand: {missing_d}")

        missing_f = req_forecast_cols - set(df_forecast.columns)
        if missing_f:
            raise KeyError(f"Missing required columns in forecast results: {missing_f}")

        # Choose valid expected demand column
        if self.expected_demand_col not in df_forecast.columns:
            fallback_cols = [
                "pred_hybrid",
                "pred_ensemble",
                "pred_lgb",
                "pred_xgb",
                "pred_hist_gbt",
                "pred_prophet",
                "pred_ridge",
                "pred_sba",
                "pred_ma_7",
            ]
            found = False
            for col in fallback_cols:
                if col in df_forecast.columns:
                    logger.warning(
                        f"Specified expected column '{self.expected_demand_col}' not in forecast. "
                        f"Falling back to available column '{col}'."
                    )
                    self.expected_demand_col = col
                    found = True
                    break
            if not found:
                raise KeyError(
                    f"Could not find any suitable forecast column in forecast_results.csv. "
                    f"Available: {df_forecast.columns.tolist()}"
                )

        self.stats["records_loaded_demand"] = len(df_demand)
        self.stats["records_loaded_forecast"] = len(df_forecast)

        return df_demand, df_forecast

    def join_and_compute_rolling(
        self,
        df_demand: pd.DataFrame,
        df_forecast: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Computes 14-day backward rolling statistics per product-city series in DuckDB 
        (preventing future lookahead leakage) and inner-joins with expected forecast demand.
        """
        logger.info("Computing backward-looking rolling baselines and joining with forecast data via DuckDB...")
        con = duckdb.connect()

        con.register("demand_src", df_demand)
        con.register("forecast_src", df_forecast)

        query = f"""
        WITH rolling_history AS (
            SELECT 
                CAST(date_ AS VARCHAR) AS date_,
                CAST(product_id AS BIGINT) AS product_id,
                CAST(city_name AS VARCHAR) AS city_name,
                CAST(daily_quantity AS DOUBLE) AS actual_demand,
                -- 14-day backward rolling window strictly excluding current day
                AVG(daily_quantity) OVER w AS rolling_mean_14,
                STDDEV(daily_quantity) OVER w AS rolling_std_14,
                COUNT(daily_quantity) OVER w AS history_count
            FROM demand_src
            WINDOW w AS (
                PARTITION BY product_id, city_name 
                ORDER BY CAST(date_ AS DATE) 
                ROWS BETWEEN {self.rolling_window} PRECEDING AND 1 PRECEDING
            )
        ),
        forecast_selection AS (
            SELECT 
                CAST(date_ AS VARCHAR) AS date_,
                CAST(product_id AS BIGINT) AS product_id,
                CAST(city_name AS VARCHAR) AS city_name,
                CAST({self.expected_demand_col} AS DOUBLE) AS expected_demand
            FROM forecast_src
        )
        SELECT 
            f.date_,
            f.product_id,
            f.city_name,
            r.actual_demand,
            f.expected_demand,
            r.rolling_mean_14,
            COALESCE(r.rolling_std_14, 0.0) AS rolling_std_14,
            COALESCE(r.history_count, 0) AS history_count
        FROM forecast_selection f
        INNER JOIN rolling_history r
            ON f.date_ = r.date_
           AND f.product_id = r.product_id
           AND f.city_name = r.city_name
        ORDER BY f.date_, f.product_id, f.city_name
        """

        merged_df = con.execute(query).df()
        con.close()

        matched_count = len(merged_df)
        unmatched_forecast = self.stats["records_loaded_forecast"] - matched_count
        unmatched_demand = self.stats["records_loaded_demand"] - matched_count

        self.stats["records_matched"] = matched_count
        self.stats["records_unmatched_forecast"] = unmatched_forecast
        self.stats["records_unmatched_demand"] = unmatched_demand
        self.stats["records_dropped_invalid"] = 0

        logger.info(
            f"Join completed: {matched_count:,} matched records. "
            f"Unmatched forecasts: {unmatched_forecast:,}; "
            f"Unmatched demand records (outside 10-day evaluation split): {unmatched_demand:,}."
        )

        return merged_df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates features required for statistical and ML anomaly detection:
        - residual = actual_demand - expected_demand
        - relative_residual = residual / expected_demand (safe division)
        - rolling_volatility = rolling_std_14
        - sales_volume = actual_demand
        """
        logger.info("Engineering anomaly features: residual, relative residual, rolling volatility, sales volume...")
        df = df.copy()

        # Clean numeric conversions
        df["actual_demand"] = pd.to_numeric(df["actual_demand"], errors="coerce").fillna(0.0)
        df["expected_demand"] = pd.to_numeric(df["expected_demand"], errors="coerce").fillna(0.0)

        # 1. Residual
        df["residual"] = df["actual_demand"] - df["expected_demand"]

        # 2. Relative residual (safely handled when expected_demand is 0)
        df["relative_residual"] = np.where(
            df["expected_demand"] > 0,
            df["residual"] / df["expected_demand"],
            np.where(df["actual_demand"] > 0, 1.0, 0.0)
        )

        # 3. Rolling Volatility
        df["rolling_volatility"] = df["rolling_std_14"].fillna(0.0)

        # 4. Sales volume
        df["sales_volume"] = df["actual_demand"]

        return df

    def detect_rolling_zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates Rolling Z-Score with 14-day history.
        Handles:
        - Fewer than minimum history observations (sets Z=0.0)
        - Zero rolling standard deviation (constant demand -> Z=0.0)
        - Flags abs(Z) > z_threshold
        """
        logger.info(f"Computing Rolling Z-Scores (threshold |Z| > {self.z_threshold})...")
        df = df.copy()

        valid_history = df["history_count"] >= self.min_history_days
        has_variance = df["rolling_volatility"] > 1e-6

        # Calculate Z-score safely
        z_score = np.zeros(len(df), dtype=float)
        mask = valid_history & has_variance

        z_score[mask] = (
            df.loc[mask, "actual_demand"] - df.loc[mask, "rolling_mean_14"]
        ) / df.loc[mask, "rolling_volatility"]

        # Edge case: std == 0, but actual differs from historical mean
        zero_var_mask = valid_history & (~has_variance)
        diff_from_mean = df.loc[zero_var_mask, "actual_demand"] - df.loc[zero_var_mask, "rolling_mean_14"]
        # If demand was constant and suddenly jumped or dropped, flag proportional to jump
        z_score[zero_var_mask] = np.where(
            diff_from_mean > 0,
            np.clip(diff_from_mean / (df.loc[zero_var_mask, "rolling_mean_14"] + 1.0), 0.0, 5.0),
            np.where(
                diff_from_mean < 0,
                -np.clip(np.abs(diff_from_mean) / (df.loc[zero_var_mask, "rolling_mean_14"] + 1.0), 0.0, 5.0),
                0.0
            )
        )

        df["z_score"] = np.round(z_score, 4)
        df["is_zscore_anomaly"] = np.abs(df["z_score"]) > self.z_threshold

        logger.info(f"Rolling Z-Score flagged {df['is_zscore_anomaly'].sum():,} anomalies.")
        return df

    def detect_isolation_forest(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fits Scikit-Learn Isolation Forest on multi-dimensional residual and volatility features:
        - residual
        - rolling_volatility
        - sales_volume
        Produces:
        - is_isolation_anomaly (bool)
        - anomaly_score (normalized float between 0.0 and 1.0, where 1.0 is maximum anomaly)
        """
        logger.info(
            f"Fitting Isolation Forest (contamination={self.contamination}, "
            f"random_state={self.random_state})..."
        )
        df = df.copy()

        feature_cols = ["residual", "rolling_volatility", "sales_volume"]
        X = df[feature_cols].copy().fillna(0.0).values

        self.iso_model = IsolationForest(
            contamination=self.contamination,
            random_state=self.random_state,
            n_estimators=100
        )
        self.iso_model.fit(X)

        # Predictions (-1 = anomaly, 1 = inlier)
        preds = self.iso_model.predict(X)
        df["is_isolation_anomaly"] = preds == -1

        # Decision function: lower values mean more abnormal
        raw_scores = self.iso_model.decision_function(X)
        df["iso_raw_score"] = raw_scores

        # Normalize score into [0.0, 1.0] scale where higher = more anomalous
        min_s = float(raw_scores.min())
        max_s = float(raw_scores.max())
        score_range = max_s - min_s if max_s > min_s else 1.0

        # Invert so higher score represents stronger anomaly
        norm_score = 1.0 - (raw_scores - min_s) / score_range
        df["anomaly_score"] = np.round(np.clip(norm_score, 0.0, 1.0), 4)

        logger.info(f"Isolation Forest flagged {df['is_isolation_anomaly'].sum():,} anomalies.")
        return df

    def combine_and_classify(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Combines Isolation Forest and Rolling Z-Score signals.
        Applies taxonomy:
        - SPIKE_DEMAND: Actual demand significantly above expected/baseline
        - DROP_STOCKOUT: Actual demand sharply below forecast or near zero
        - PRICE_ANOMALY: Documented as unavailable (0 count) due to lack of price time series
        """
        logger.info("Combining anomaly signals and applying taxonomy classification...")
        df = df.copy()

        # Combined detection: either statistical Z-Score threshold or Isolation Forest outlier
        df["is_anomaly"] = df["is_zscore_anomaly"] | df["is_isolation_anomaly"]

        # Filter to candidate anomalies
        anomalies_df = df[df["is_anomaly"]].copy()

        # Classification rule:
        # If residual > 0 or Z-score > 0, demand was higher than expected -> SPIKE_DEMAND
        # If residual < 0 or Z-score < 0, demand fell below expected -> DROP_STOCKOUT
        is_spike = (anomalies_df["residual"] > 0) | (anomalies_df["z_score"] > self.z_threshold)
        anomalies_df["anomaly_type"] = np.where(is_spike, "SPIKE_DEMAND", "DROP_STOCKOUT")

        logger.info(
            f"Classified {len(anomalies_df):,} total anomalies: "
            f"{(anomalies_df['anomaly_type'] == 'SPIKE_DEMAND').sum():,} SPIKE_DEMAND, "
            f"{(anomalies_df['anomaly_type'] == 'DROP_STOCKOUT').sum():,} DROP_STOCKOUT, "
            f"0 PRICE_ANOMALY (Price time-series data not present)."
        )

        return anomalies_df

    def assign_severity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns deterministic severity levels (CRITICAL, MEDIUM, LOW) based on:
        - Z-score magnitude
        - Absolute and relative residual magnitude
        - Algorithm consensus (both Z-score and Isolation Forest)
        - Extreme stockout drops (actual near zero when forecast was large)
        """
        logger.info("Assigning deterministic severity levels (CRITICAL, MEDIUM, LOW)...")
        df = df.copy()

        def compute_severity(row) -> str:
            abs_z = abs(row["z_score"])
            abs_res = abs(row["residual"])
            actual = row["actual_demand"]
            expected = row["expected_demand"]
            both_flagged = row["is_zscore_anomaly"] and row["is_isolation_anomaly"]

            # -------------------------------------------------------------
            # 1. CRITICAL RULES (Strongest Actionable Anomalies)
            # -------------------------------------------------------------
            # a) Extreme statistical Z-score
            if abs_z >= 4.0:
                return "CRITICAL"

            # b) Dual algorithm agreement with substantial magnitude
            if both_flagged and abs_res >= 100.0 and abs_z >= 3.0:
                return "CRITICAL"

            # c) Severe stockout drop: near zero actual demand despite large forecast
            if actual <= 10.0 and expected >= 150.0:
                return "CRITICAL"

            # d) Severe spike: massive demand surge exceeding 300 units above expectation
            if row["residual"] >= 300.0 and abs_z >= 3.5:
                return "CRITICAL"

            # -------------------------------------------------------------
            # 2. MEDIUM RULES (Clear Operational Anomalies)
            # -------------------------------------------------------------
            # a) Standard statistical Z-score exceedance
            if abs_z >= 2.8:
                return "MEDIUM"

            # b) Isolation Forest anomaly with noticeable residual
            if row["is_isolation_anomaly"] and abs_res >= 75.0:
                return "MEDIUM"

            # c) Substantial drop: actual demand < 30% of expected
            if actual < 0.3 * expected and expected >= 100.0:
                return "MEDIUM"

            # -------------------------------------------------------------
            # 3. LOW RULES (Mild Statistical Deviations)
            # -------------------------------------------------------------
            return "LOW"

        df["severity"] = df.apply(compute_severity, axis=1)

        counts = df["severity"].value_counts().to_dict()
        logger.info(
            f"Severity distribution: CRITICAL={counts.get('CRITICAL', 0):,}, "
            f"MEDIUM={counts.get('MEDIUM', 0):,}, LOW={counts.get('LOW', 0):,}."
        )

        return df

    def generate_recommendations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns operational action recommendations.
        Recommendations are operational suggestions, NOT claims about confirmed cause.
        """
        logger.info("Generating operational action recommendations...")
        df = df.copy()

        recommendations = {
            "SPIKE_DEMAND": "Review inventory availability and prepare replenishment.",
            "DROP_STOCKOUT": "Check inventory, stock availability, and delivery/supply status.",
            "PRICE_ANOMALY": "Review recent price or discount changes."
        }

        df["action_recommendation"] = df["anomaly_type"].map(
            lambda t: recommendations.get(t, "Investigate demand deviation against operational baseline.")
        )

        return df

    def export_anomalies(
        self,
        df: pd.DataFrame,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Exports final anomalies dataframe adhering to exact required contract schema:
        - date_
        - product_id
        - city_name
        - actual_demand
        - expected_demand
        - anomaly_score
        - anomaly_type
        - severity
        - action_recommendation

        Sorted by severity (CRITICAL first, then MEDIUM, then LOW) and date_ descending.
        """
        target_path = output_path or self.output_csv
        target_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exporting anomaly deliverables to: {target_path}")

        # Exact contract columns
        contract_cols = [
            "date_",
            "product_id",
            "city_name",
            "actual_demand",
            "expected_demand",
            "anomaly_score",
            "anomaly_type",
            "severity",
            "action_recommendation"
        ]

        export_df = df[contract_cols].copy()

        # Deterministic formatting
        export_df["product_id"] = export_df["product_id"].astype(str)
        export_df["actual_demand"] = np.round(export_df["actual_demand"].astype(float), 2)
        export_df["expected_demand"] = np.round(export_df["expected_demand"].astype(float), 2)
        export_df["anomaly_score"] = np.round(export_df["anomaly_score"].astype(float), 4)

        # Custom sorting: CRITICAL first, then MEDIUM, then LOW, then date_ descending
        severity_order = {"CRITICAL": 0, "MEDIUM": 1, "LOW": 2}
        export_df["_sev_rank"] = export_df["severity"].map(severity_order)
        export_df = export_df.sort_values(by=["_sev_rank", "date_", "product_id"], ascending=[True, False, True])
        export_df = export_df.drop(columns=["_sev_rank"])

        # Check for duplicates
        dups = export_df.duplicated(subset=["date_", "product_id", "city_name"]).sum()
        if dups > 0:
            logger.warning(f"Found {dups} duplicate records in export. Deduplicating...")
            export_df = export_df.drop_duplicates(subset=["date_", "product_id", "city_name"], keep="first")

        export_df.to_csv(target_path, index=False)
        logger.info(f"Successfully wrote {len(export_df):,} anomaly records to {target_path}")

        # Update final stats
        self.stats["total_anomalies_detected"] = len(export_df)
        self.stats["spike_demand_count"] = int((export_df["anomaly_type"] == "SPIKE_DEMAND").sum())
        self.stats["drop_stockout_count"] = int((export_df["anomaly_type"] == "DROP_STOCKOUT").sum())
        self.stats["price_anomaly_count"] = int((export_df["anomaly_type"] == "PRICE_ANOMALY").sum())
        self.stats["critical_count"] = int((export_df["severity"] == "CRITICAL").sum())
        self.stats["medium_count"] = int((export_df["severity"] == "MEDIUM").sum())
        self.stats["low_count"] = int((export_df["severity"] == "LOW").sum())

        return target_path

    def run_pipeline(self) -> Dict[str, Any]:
        """
        Executes end-to-end anomaly detection pipeline and returns run statistics.
        """
        logger.info("=" * 80)
        logger.info("STARTING ML ANOMALY & OUTLIER DETECTION ENGINE")
        logger.info("=" * 80)

        # 1. Load Data
        df_demand, df_forecast = self.load_data()

        # 2. Join and Rolling Statistics
        df_joined = self.join_and_compute_rolling(df_demand, df_forecast)

        # 3. Feature Engineering
        df_features = self.engineer_features(df_joined)

        # 4. Rolling Z-Score
        df_z = self.detect_rolling_zscore(df_features)

        # 5. Isolation Forest
        df_iso = self.detect_isolation_forest(df_z)

        # 6. Combine and Classify
        df_classified = self.combine_and_classify(df_iso)

        # 7. Assign Severity
        df_severity = self.assign_severity(df_classified)

        # 8. Generate Recommendations
        df_final = self.generate_recommendations(df_severity)

        # 9. Export CSV Deliverable
        self.export_anomalies(df_final)

        logger.info("=" * 80)
        logger.info("ANOMALY DETECTION PIPELINE SUMMARY")
        logger.info("=" * 80)
        for k, v in self.stats.items():
            logger.info(f"  {k}: {v}")
        logger.info("=" * 80)

        return self.stats


def run():
    detector = DemandAnomalyDetector()
    return detector.run_pipeline()


if __name__ == "__main__":
    run()
