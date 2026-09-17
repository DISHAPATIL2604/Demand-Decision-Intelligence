"""Populate forecast_evaluations from real PostgreSQL forecasts and demand."""

from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.db.session import engine


MATCHED_FORECASTS_SQL = text("""
    SELECT COUNT(*)
    FROM forecasts AS f
    JOIN daily_product_demand AS d
      ON d.product_id = f.product_id
     AND d.city_name = f.city_name
     AND d.date_ = f.forecast_date
""")

DELETE_EXISTING_EVALUATIONS_SQL = text("""
    DELETE FROM forecast_evaluations AS e
    WHERE EXISTS (SELECT 1 FROM forecasts AS f WHERE f.run_id = e.run_id)
""")

INSERT_EVALUATIONS_SQL = text("""
    INSERT INTO forecast_evaluations (
        run_id, product_id, city_name, model_name, mae, rmse, mape, wape
    )
    SELECT
        f.run_id,
        f.product_id,
        f.city_name,
        COALESCE(NULLIF(f.model_name, ''), r.model_name) AS model_name,
        AVG(ABS(d.total_quantity - f.predicted_demand)) AS mae,
        SQRT(AVG(POWER(d.total_quantity - f.predicted_demand, 2))) AS rmse,
        AVG(
            CASE WHEN d.total_quantity <> 0
                 THEN ABS((d.total_quantity - f.predicted_demand) / d.total_quantity) * 100
            END
        ) AS mape,
        CASE WHEN SUM(ABS(d.total_quantity)) <> 0
             THEN SUM(ABS(d.total_quantity - f.predicted_demand))
                  / SUM(ABS(d.total_quantity)) * 100
        END AS wape
    FROM forecasts AS f
    JOIN daily_product_demand AS d
      ON d.product_id = f.product_id
     AND d.city_name = f.city_name
     AND d.date_ = f.forecast_date
    JOIN forecast_runs AS r ON r.id = f.run_id
    GROUP BY
        f.run_id, f.product_id, f.city_name,
        COALESCE(NULLIF(f.model_name, ''), r.model_name)
""")

SUMMARY_SQL = text("""
    SELECT
        COUNT(*) AS total_evaluation_rows,
        COUNT(DISTINCT model_name) AS distinct_models,
        COUNT(DISTINCT run_id) AS distinct_forecast_runs
    FROM forecast_evaluations
""")

MODEL_METRICS_SQL = text("""
    SELECT
        model_name,
        AVG(mae) AS average_mae,
        AVG(rmse) AS average_rmse,
        AVG(wape) AS average_wape
    FROM forecast_evaluations
    GROUP BY model_name
    ORDER BY model_name
""")


def main() -> None:
    with engine.connect() as connection:
        matched_forecasts = connection.execute(MATCHED_FORECASTS_SQL).scalar_one()
    print(f"Forecast rows with real demand matches: {matched_forecasts}")

    with engine.begin() as connection:
        deleted = connection.execute(DELETE_EXISTING_EVALUATIONS_SQL).rowcount
        inserted = connection.execute(INSERT_EVALUATIONS_SQL).rowcount
    print(f"Existing evaluation rows rebuilt: {deleted}")
    print(f"Evaluation rows inserted: {inserted}")

    with engine.connect() as connection:
        summary = connection.execute(SUMMARY_SQL).mappings().one()
        model_metrics = connection.execute(MODEL_METRICS_SQL).mappings().all()
    print(f"Total forecast_evaluations rows: {summary['total_evaluation_rows']}")
    print(f"Distinct models: {summary['distinct_models']}")
    print(f"Distinct forecast runs: {summary['distinct_forecast_runs']}")
    for row in model_metrics:
        print(
            f"{row['model_name']}: "
            f"average_mae={row['average_mae']}, "
            f"average_rmse={row['average_rmse']}, "
            f"average_wape={row['average_wape']}"
        )


if __name__ == "__main__":
    main()
