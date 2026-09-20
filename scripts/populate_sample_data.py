"""
Populate Sample Data Script
Ingests sample sales, aggregates daily demand, generates multi-model forecasts,
populates inventory simulation states and recommendations, and inserts anomaly alerts.
"""

import sys
import json
import csv
from datetime import datetime, date, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.db.session import SessionLocal, engine
from backend.models.product import Product
from backend.models.upload import UploadJob, ValidationResult
from backend.models.sales import SalesTransaction
from backend.models.demand import DailyProductDemand
from backend.models.forecast import ForecastRun, ForecastItem, ForecastEvaluation
from backend.models.inventory import InventoryState, InventoryRecommendation
from backend.models.anomaly import AnomalyAlert

def populate_all():
    db: Session = SessionLocal()
    try:
        print("--- Step 1: Ingesting Sample Sales Transactions ---")
        sales_csv = BASE_DIR / "sample_sales_upload.csv"
        if not sales_csv.exists():
            print(f"File {sales_csv} does not exist.")
            return

        # Ensure upload job exists
        upload_job = UploadJob(
            filename="sample_sales_upload.csv",
            file_type="sales",
            file_size_bytes=sales_csv.stat().st_size,
            status="COMPLETED",
            total_rows=8,
            processed_rows=8,
            completed_at=datetime.utcnow(),
        )
        db.add(upload_job)
        db.commit()
        db.refresh(upload_job)

        # Add validation checks
        val_checks = [
            ("required_columns", "PASS", "All required columns are present."),
            ("date_validation", "PASS", "Missing dates: 0; Invalid dates: 0"),
            ("product_id_validation", "PASS", "All product IDs matched."),
            ("quantity_validation", "PASS", "Valid positive procured quantities."),
            ("price_validation", "PASS", "Valid positive unit prices."),
        ]
        for name, status, details in val_checks:
            db.add(ValidationResult(upload_id=upload_job.id, check_name=name, status=status, details=details))
        db.commit()

        # Ingest transactions
        sales_df = pd.read_csv(sales_csv)
        for _, row in sales_df.iterrows():
            p_id = int(row["product_id"])
            prod = db.query(Product).filter(Product.product_id == p_id).first()
            if not prod:
                prod = Product(
                    product_id=p_id,
                    product_name=f"Sample Product #{p_id}",
                    unit="Pack",
                    l0_category="Groceries & Food",
                    l1_category="Staples",
                    is_active=True
                )
                db.add(prod)
                db.commit()

            tx = SalesTransaction(
                upload_id=upload_job.id,
                date_=datetime.strptime(str(row["date_"]).strip(), "%Y-%m-%d").date(),
                city_name=str(row["city_name"]).strip(),
                order_id=str(row["order_id"]).strip(),
                cart_id=str(row["cart_id"]).strip(),
                dim_customer_key=str(row["dim_customer_key"]).strip(),
                procured_quantity=float(row["procured_quantity"]),
                unit_selling_price=float(row["unit_selling_price"]),
                total_discount_amount=float(row.get("total_discount_amount", 0.0)),
                product_id=p_id,
                total_weighted_landing_price=float(row.get("total_weighted_landing_price", 0.0)),
            )
            db.add(tx)
        db.commit()
        print("Ingested sample sales transactions into 'sales'.")

        print("--- Step 2: Aggregating into Daily Product Demand ---")
        base_date = date(2026, 4, 1)
        key_skus = [
            (19512, "Delhi", "Fortune Sunlite Refined Sunflower Oil 1L", "Groceries & Food", 8690.0, 115.0),
            (391306, "Bengaluru", "Aashirvaad Superior MP Sharbati Atta 5kg", "Groceries & Food", 6420.0, 245.0),
            (12872, "Mumbai", "Tata Salt Vacuum Evaporated 1kg", "Groceries & Food", 5310.0, 28.0),
            (3881, "HR-NCR", "Amul Butter Pasteurised 500g", "Groceries & Food", 4890.0, 275.0),
            (445675, "Delhi", "Maggi 2-Minute Instant Noodles 280g", "Groceries & Food", 4120.0, 56.0),
            (1, "Delhi", "Dettol Original Liquid Handwash Refill 750ml", "Personal Care", 3250.0, 120.0),
            (476763, "Bengaluru", "Surf Excel Easy Wash Detergent Powder 1kg", "Household Essentials", 1850.0, 145.0),
            (483436, "Bengaluru", "Colgate Strong Teeth Dental Cream 500g", "Personal Care", 1420.0, 210.0),
            (476825, "Mumbai", "Taj Mahal Tea 500g", "Groceries & Food", 980.0, 360.0),
            (483438, "Delhi", "Parle-G Gold Biscuits 1kg", "Groceries & Food", 2200.0, 90.0)
        ]

        for p_id, city, p_name, cat, mean_demand, unit_p in key_skus:
            prod = db.query(Product).filter(Product.product_id == p_id).first()
            if not prod:
                db.add(Product(
                    product_id=p_id,
                    product_name=p_name,
                    unit="Standard Pack",
                    l0_category=cat,
                    is_active=True
                ))
                db.commit()

            for day_offset in range(14):
                cur_date = base_date - timedelta(days=(13 - day_offset))
                exists = db.query(DailyProductDemand).filter(
                    DailyProductDemand.product_id == p_id,
                    DailyProductDemand.city_name == city,
                    DailyProductDemand.date_ == cur_date
                ).first()
                if not exists:
                    day_factor = 1.25 if cur_date.weekday() in (5, 6) else 0.95
                    qty = round(mean_demand * day_factor * float(np.random.uniform(0.92, 1.08)), 1)
                    val = round(qty * unit_p, 2)
                    disc = round(val * 0.06, 2)
                    db.add(DailyProductDemand(
                        date_=cur_date,
                        product_id=p_id,
                        city_name=city,
                        total_quantity=qty,
                        total_sales_value=val,
                        total_discount_value=disc,
                        avg_unit_price=unit_p,
                        order_count=int(max(1, qty / 2.5))
                    ))
        db.commit()
        print("Daily demand aggregated.")

        print("--- Step 3: Generating Forecast Runs & Forecasts ---")
        models = [
            ("Prophet (Weekly Seasonality)", 14.2, 5.2, 38.6),
            ("Moving Average (7-Day)", 22.8, 8.4, 52.1),
            ("LightGBM Regressor", 16.5, 6.1, 41.2),
            ("Naive Baseline", 28.5, 11.2, 64.3)
        ]

        for model_name, wape, mae, rmse in models:
            run = ForecastRun(
                model_name=model_name,
                horizon_days=14,
                status="COMPLETED",
                start_date=base_date,
                end_date=base_date + timedelta(days=14),
                metrics_summary=json.dumps({"wape": wape, "mae": mae, "rmse": rmse}),
                completed_at=datetime.utcnow()
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            # 1 overall evaluation per run_id
            db.add(ForecastEvaluation(
                run_id=run.id,
                city_name="ALL",
                model_name=model_name,
                mae=mae,
                rmse=rmse,
                wape=wape,
                mape=round(wape * 0.9, 2)
            ))

            for p_id, city, _, _, mean_demand, _ in key_skus[:6]:
                for f_day in range(1, 15):
                    f_date = base_date + timedelta(days=f_day)
                    yhat = round(mean_demand * (1.0 + f_day * 0.01) * float(np.random.uniform(0.96, 1.04)), 1)
                    db.add(ForecastItem(
                        run_id=run.id,
                        product_id=p_id,
                        city_name=city,
                        forecast_date=f_date,
                        predicted_demand=yhat,
                        lower_bound=round(yhat * 0.85, 1),
                        upper_bound=round(yhat * 1.15, 1),
                        model_name=model_name
                    ))
        db.commit()
        print("Seeded forecast runs, items, and evaluations.")

        print("--- Step 4: Populating Inventory Recommendations & Simulation ---")
        inv_csv = BASE_DIR / "reports" / "inventory_decision_sample.csv"
        rec_data = []
        if inv_csv.exists():
            df_inv = pd.read_csv(inv_csv)
            rec_data = df_inv.head(50).to_dict(orient="records")

        for r in rec_data:
            p_id = int(r["product_id"])
            city = str(r["city_name"])
            prod = db.query(Product).filter(Product.product_id == p_id).first()
            if not prod:
                db.add(Product(product_id=p_id, product_name=f"Catalog Item #{p_id}", is_active=True))
                db.commit()

            mean_dem = float(r.get("mean_daily_demand", 100))
            ss = float(r.get("safety_stock", 50))
            rop = float(r.get("reorder_point", 150))
            tsl = float(r.get("target_stock_level", 250))
            lead_time = int(r.get("lead_time_days_param", 3))

            curr_stock = round(rop * float(np.random.uniform(0.4, 1.6)), 1)
            risk_status = "OPTIMAL"
            priority = "LOW"
            rec_order_qty = 0.0

            if curr_stock < ss:
                risk_status = "CRITICAL_STOCKOUT"
                priority = "HIGH"
                rec_order_qty = round(tsl - curr_stock, 1)
            elif curr_stock <= rop:
                risk_status = "REORDER_RECOMMENDED"
                priority = "MEDIUM"
                rec_order_qty = round(tsl - curr_stock, 1)
            elif curr_stock > tsl * 1.4:
                risk_status = "OVERSTOCK"
                priority = "LOW"

            db.add(InventoryRecommendation(
                product_id=p_id,
                city_name=city,
                calculation_date=base_date,
                current_stock=curr_stock,
                avg_daily_demand=mean_dem,
                lead_time_days=lead_time,
                safety_stock=ss,
                reorder_point=rop,
                recommended_order_qty=rec_order_qty,
                risk_status=risk_status,
                priority=priority
            ))

            sim_opening = curr_stock + (mean_dem * 5)
            for d in range(7):
                s_date = base_date - timedelta(days=(6 - d))
                sales_q = round(mean_dem * float(np.random.uniform(0.9, 1.1)), 1)
                received_q = round(mean_dem * 3) if d == 3 else 0.0
                closing_q = max(0.0, round(sim_opening + received_q - sales_q, 1))

                exists_sim = db.query(InventoryState).filter(
                    InventoryState.product_id == p_id,
                    InventoryState.city_name == city,
                    InventoryState.snapshot_date == s_date
                ).first()
                if not exists_sim:
                    db.add(InventoryState(
                        product_id=p_id,
                        city_name=city,
                        snapshot_date=s_date,
                        opening_stock=sim_opening,
                        stock_received=received_q,
                        sales_quantity=sales_q,
                        closing_stock=closing_q,
                        is_simulated=True
                    ))
                sim_opening = closing_q

        db.commit()
        print("Inventory recommendations and simulation states populated.")

        print("--- Step 5: Populating Demand Anomaly Alerts ---")
        anom_csv = BASE_DIR / "reports" / "demand_anomalies.csv"
        if anom_csv.exists():
            df_anom = pd.read_csv(anom_csv)
            for _, r in df_anom.head(100).iterrows():
                p_id = int(r["product_id"])
                city = str(r["city_name"])
                prod = db.query(Product).filter(Product.product_id == p_id).first()
                if not prod:
                    db.add(Product(product_id=p_id, product_name=f"Catalog Item #{p_id}", is_active=True))
                    db.commit()

                a_date = datetime.strptime(str(r["date_"]).strip(), "%Y-%m-%d").date()
                db.add(AnomalyAlert(
                    product_id=p_id,
                    city_name=city,
                    anomaly_date=a_date,
                    anomaly_type=str(r["anomaly_type"]),
                    severity=str(r.get("severity", "MEDIUM")),
                    metric_name="demand_quantity",
                    actual_value=float(r["actual_demand"]),
                    expected_value=float(r.get("expected_demand", 0.0)),
                    description=f"{r.get('action_recommendation', 'Anomaly detected in sales volume.')}",
                    status="OPEN"
                ))
            db.commit()
            print("Populated anomaly alerts into PostgreSQL.")

        print("\n=== ALL SAMPLE DATA SUCCESSFULLY POPULATED INTO POSTGRESQL ===")

    except Exception as e:
        db.rollback()
        print(f"Error populating sample data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    populate_all()
