import csv
import io
from pathlib import Path

import psycopg2


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_URL = "postgresql://postgres:disha@localhost:5432/demand_decision_db"

PRODUCT_FILE = (
    PROJECT_ROOT
    / "dataset"
    / "raw"
    / "products"
    / "dim_product.csv"
)

REAL_DEMAND_FILE = Path(
    r"C:\Users\krish\Downloads\dataset\daily_product_demand.csv"
)

FORECAST_FILE = (
    PROJECT_ROOT
    / "reports"
    / "forecast_results.csv"
)


def connect():
    return psycopg2.connect(DATABASE_URL)


# =========================================================
# FIND PRODUCT IDS THAT ARE PRESENT IN REAL DEMAND
# =========================================================

def find_missing_products():

    print("\nChecking product ID coverage...")

    catalog_ids = set()

    with open(
        PRODUCT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:
            catalog_ids.add(int(row["product_id"]))

    demand_ids = set()
    missing_products = {}

    with open(
        REAL_DEMAND_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            pid = int(row["product_id"])

            if pid not in catalog_ids:

                demand_ids.add(pid)

                # Keep the first real product information
                # encountered for this missing product.
                if pid not in missing_products:
                    missing_products[pid] = {
                        "product_name": row["product_name"],
                        "l0_category": row["l0_category"],
                        "l1_category": row["l1_category"],
                        "l2_category": row["l2_category"],
                    }

    print(f"Catalog product IDs : {len(catalog_ids):,}")
    print(f"Demand product IDs  : {len(demand_ids) + len(catalog_ids & demand_ids):,}")
    print(f"Missing product IDs : {len(missing_products):,}")

    return missing_products


# =========================================================
# PRODUCTS
# =========================================================

def load_products(conn, missing_products):

    print("\n[1/3] Loading products...")

    cur = conn.cursor()

    cur.execute("TRUNCATE TABLE products CASCADE")

    # -----------------------------------------------------
    # Main product master
    # -----------------------------------------------------

    with open(
        PRODUCT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        output = io.StringIO()
        writer = csv.writer(output)

        for row in reader:

            writer.writerow([
                row["product_id"],
                row["product_name"],
                row.get("unit") or "",
                row.get("product_type") or "",
                row.get("brand_name") or "",
                row.get("manufacturer_name") or "",
                row.get("l0_category") or "",
                row.get("l1_category") or "",
                row.get("l2_category") or "",
                row.get("l0_category_id") or "",
                row.get("l1_category_id") or "",
                row.get("l2_category_id") or "",
            ])

        output.seek(0)

        cur.copy_expert(
            """
            COPY products (
                product_id,
                product_name,
                unit,
                product_type,
                brand_name,
                manufacturer_name,
                l0_category,
                l1_category,
                l2_category,
                l0_category_id,
                l1_category_id,
                l2_category_id
            )
            FROM STDIN
            WITH (FORMAT CSV, NULL '')
            """,
            output,
        )

    print("Main product catalog loaded.")

    # -----------------------------------------------------
    # Missing products
    #
    # These are derived ONLY from real demand records.
    # No synthetic values are created.
    # -----------------------------------------------------

    if missing_products:

        output = io.StringIO()
        writer = csv.writer(output)

        for pid, data in missing_products.items():

            writer.writerow([
                pid,
                data["product_name"] or f"Unknown Product (ID {pid})",
                "",
                "",
                "",
                "",
                data["l0_category"] or "",
                data["l1_category"] or "",
                data["l2_category"] or "",
                "",
                "",
                "",
            ])

        output.seek(0)

        cur.copy_expert(
            """
            COPY products (
                product_id,
                product_name,
                unit,
                product_type,
                brand_name,
                manufacturer_name,
                l0_category,
                l1_category,
                l2_category,
                l0_category_id,
                l1_category_id,
                l2_category_id
            )
            FROM STDIN
            WITH (FORMAT CSV, NULL '')
            """,
            output,
        )

        print(
            f"Added {len(missing_products):,} "
            "real demand-referenced products."
        )

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")

    count = cur.fetchone()[0]

    print(f"Total products in PostgreSQL: {count:,}")

    cur.close()


# =========================================================
# STREAM REAL DAILY DEMAND
# =========================================================

class DemandCSVStream:

    def __init__(self, filename):

        self.file = open(
            filename,
            "r",
            encoding="utf-8-sig",
            newline=""
        )

        self.reader = csv.DictReader(self.file)

        self.buffer = b""
        self.finished = False

    def _next_output_line(self):

        try:
            row = next(self.reader)

        except StopIteration:
            return None

        quantity = float(row["daily_quantity"])
        revenue = float(row["daily_revenue"])

        if quantity > 0:
            avg_unit_price = revenue / quantity
        else:
            avg_unit_price = None

        output = io.StringIO()

        writer = csv.writer(output)

        writer.writerow([
            row["date_"],
            row["product_id"],
            row["city_name"],
            quantity,
            revenue,
            "",
            avg_unit_price if avg_unit_price is not None else "",
            row["order_count"],
        ])

        return output.getvalue().encode("utf-8")

    def read(self, size=-1):

        if self.finished and not self.buffer:
            return b""

        if size == -1:

            chunks = []

            while True:

                line = self._next_output_line()

                if line is None:

                    self.finished = True
                    break

                chunks.append(line)

            return b"".join(chunks)

        while len(self.buffer) < size:

            line = self._next_output_line()

            if line is None:

                self.finished = True
                break

            self.buffer += line

        result = self.buffer[:size]

        self.buffer = self.buffer[size:]

        return result

    def close(self):

        self.file.close()


# =========================================================
# DAILY DEMAND
# =========================================================

def load_daily_demand(conn):

    print("\n[2/3] Loading REAL daily demand...")
    print(f"Source: {REAL_DEMAND_FILE}")

    cur = conn.cursor()

    cur.execute("""
        ALTER TABLE daily_product_demand
        ALTER COLUMN total_discount_value DROP NOT NULL
    """)

    cur.execute(
        "TRUNCATE TABLE daily_product_demand RESTART IDENTITY"
    )

    stream = DemandCSVStream(REAL_DEMAND_FILE)

    try:

        cur.copy_expert(
            """
            COPY daily_product_demand (
                date_,
                product_id,
                city_name,
                total_quantity,
                total_sales_value,
                total_discount_value,
                avg_unit_price,
                order_count
            )
            FROM STDIN
            WITH (FORMAT CSV)
            """,
            stream,
        )

    finally:

        stream.close()

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM daily_product_demand"
    )

    count = cur.fetchone()[0]

    print(f"Daily demand rows loaded: {count:,}")

    cur.close()


# =========================================================
# FORECASTS
# =========================================================

def load_forecasts(conn):

    print("\n[3/3] Loading forecast results...")

    cur = conn.cursor()

    cur.execute(
        """
        TRUNCATE TABLE
            forecasts,
            forecast_runs,
            forecast_evaluations
        RESTART IDENTITY CASCADE
        """
    )

    conn.commit()

    models = {
        "pred_naive_lag1": "Naive (Lag-1)",
        "pred_seasonal_naive_lag7": "Seasonal Naive (Lag-7)",
        "pred_ma_7": "Moving Average (7 Days)",
        "pred_ma_14": "Moving Average (14 Days)",
        "pred_ma_28": "Moving Average (28 Days)",
        "pred_prophet": "Prophet (Weekly Seasonality)",
        "pred_ridge": "Ridge Regression",
        "pred_hist_gbt": "HistGradientBoosting (GBT)",
    }

    with open(
        FORECAST_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        rows = list(reader)

    if not rows:
        raise RuntimeError("forecast_results.csv is empty")

    start_date = rows[0]["date_"]
    end_date = rows[-1]["date_"]

    print(f"Forecast period: {start_date} → {end_date}")
    print(f"Forecast rows: {len(rows):,}")

    for prediction_column, model_name in models.items():

        cur.execute(
            """
            INSERT INTO forecast_runs (
                model_name,
                horizon_days,
                status,
                start_date,
                end_date
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                model_name,
                10,
                "completed",
                start_date,
                end_date,
            ),
        )

        run_id = cur.fetchone()[0]

        output = io.StringIO()
        writer = csv.writer(output)

        for row in rows:

            value = row.get(prediction_column)

            if value in ("", None):
                continue

            prediction = max(0.0, float(value))

            writer.writerow([
                run_id,
                row["product_id"],
                row["city_name"],
                row["date_"],
                prediction,
                model_name,
            ])

        output.seek(0)

        cur.copy_expert(
            """
            COPY forecasts (
                run_id,
                product_id,
                city_name,
                forecast_date,
                predicted_demand,
                model_name
            )
            FROM STDIN
            WITH (FORMAT CSV)
            """,
            output,
        )

        print(f"  {model_name}: loaded")

    conn.commit()

    cur.execute(
        "SELECT COUNT(*) FROM forecast_runs"
    )

    runs = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM forecasts"
    )

    forecasts = cur.fetchone()[0]

    print(f"\nForecast runs: {runs}")
    print(f"Forecast records: {forecasts:,}")

    cur.close()


# =========================================================
# VERIFY
# =========================================================

def verify_database(conn):

    cur = conn.cursor()

    tables = [
        "products",
        "daily_product_demand",
        "forecast_runs",
        "forecasts",
        "forecast_evaluations",
        "inventory_recommendations",
    ]

    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)

    for table in tables:

        cur.execute(
            f"SELECT COUNT(*) FROM {table}"
        )

        count = cur.fetchone()[0]

        print(f"{table:<30} {count:>12,}")

    cur.close()


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("DEMAND-DECISION-INTELLIGENCE")
    print("POSTGRESQL DATA LOADER")
    print("=" * 60)

    missing_products = find_missing_products()

    conn = connect()

    try:

        load_products(
            conn,
            missing_products
        )

        load_daily_demand(conn)

        load_forecasts(conn)

        verify_database(conn)

        print("\n" + "=" * 60)
        print("SUCCESS: PostgreSQL seeding completed.")
        print("=" * 60)

    except Exception:

        conn.rollback()

        print(
            "\nERROR: Database transaction rolled back."
        )

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    main()