import psycopg2

DB_USER = "postgres"
DB_PASS = "Kaushal@12"
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "demand_decision_db"

try:
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname="postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Database '{DB_NAME}' CREATED successfully.")
    else:
        print(f"Database '{DB_NAME}' already exists.")
    cur.close()
    conn.close()
    print("PostgreSQL connection: OK")
except Exception as e:
    print(f"ERROR: {e}")
