-- =============================================================================
-- Demand & Decision Intelligence System - Database Schema Initialization
-- Target Database: PostgreSQL 16+
-- Compatible with: pgAdmin 4 Query Tool
-- =============================================================================

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. ROLES TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 2. USERS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- -----------------------------------------------------------------------------
-- 3. PRODUCTS (DIM_PRODUCT) MASTER TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT PRIMARY KEY,
    product_name VARCHAR(500) NOT NULL,
    unit VARCHAR(100),
    product_type VARCHAR(100),
    brand_name VARCHAR(255),
    manufacturer_name VARCHAR(500),
    l0_category VARCHAR(150),
    l1_category VARCHAR(150),
    l2_category VARCHAR(150),
    l0_category_id INTEGER,
    l1_category_id INTEGER,
    l2_category_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_name);
CREATE INDEX IF NOT EXISTS idx_products_l0_cat ON products(l0_category);
CREATE INDEX IF NOT EXISTS idx_products_l1_cat ON products(l1_category);
CREATE INDEX IF NOT EXISTS idx_products_l2_cat ON products(l2_category);

-- -----------------------------------------------------------------------------
-- 4. UPLOAD JOBS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upload_jobs (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) DEFAULT 'sales' NOT NULL,
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'PENDING' NOT NULL,
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    error_summary TEXT,
    uploaded_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_upload_jobs_status ON upload_jobs(status);

-- -----------------------------------------------------------------------------
-- 5. VALIDATION RESULTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER NOT NULL REFERENCES upload_jobs(id) ON DELETE CASCADE,
    check_name VARCHAR(150) NOT NULL,
    status VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_validation_upload_id ON validation_results(upload_id);

-- -----------------------------------------------------------------------------
-- 6. SALES TRANSACTIONS (FACT_SALES) TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sales (
    id BIGSERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES upload_jobs(id) ON DELETE SET NULL,
    date_ DATE NOT NULL,
    city_name VARCHAR(100),
    order_id VARCHAR(100),
    cart_id VARCHAR(100),
    dim_customer_key VARCHAR(100),
    procured_quantity DOUBLE PRECISION DEFAULT 1.0 NOT NULL,
    unit_selling_price DOUBLE PRECISION NOT NULL,
    total_discount_amount DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    total_weighted_landing_price DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(date_);
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_city_name ON sales(city_name);
CREATE INDEX IF NOT EXISTS idx_sales_order_id ON sales(order_id);
CREATE INDEX IF NOT EXISTS idx_sales_date_product ON sales(date_, product_id);
CREATE INDEX IF NOT EXISTS idx_sales_city_date ON sales(city_name, date_);

-- -----------------------------------------------------------------------------
-- 7. DAILY PRODUCT DEMAND (AGGREGATED TIME-SERIES GRAIN)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_product_demand (
    id BIGSERIAL PRIMARY KEY,
    date_ DATE NOT NULL,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    total_quantity DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    total_sales_value DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    total_discount_value DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    avg_unit_price DOUBLE PRECISION,
    order_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_daily_demand_date_product_city UNIQUE (date_, product_id, city_name)
);

CREATE INDEX IF NOT EXISTS idx_demand_product_date ON daily_product_demand(product_id, date_);
CREATE INDEX IF NOT EXISTS idx_demand_date ON daily_product_demand(date_);
CREATE INDEX IF NOT EXISTS idx_demand_city_product ON daily_product_demand(city_name, product_id);

-- -----------------------------------------------------------------------------
-- 8. FORECAST RUNS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecast_runs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    horizon_days INTEGER DEFAULT 14 NOT NULL,
    status VARCHAR(50) DEFAULT 'RUNNING' NOT NULL,
    start_date DATE,
    end_date DATE,
    metrics_summary TEXT,
    created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_forecast_runs_status ON forecast_runs(status);

-- -----------------------------------------------------------------------------
-- 8A. MARKET PRICES AND EXPLICIT PRODUCT-TO-COMMODITY MAPPINGS
-- Observations retain the source's price type; do not infer retail from mandi.
-- Empty geography/variety is stored as '' so the uniqueness constraint works.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_price_observations (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(40) NOT NULL,
    commodity VARCHAR(200) NOT NULL,
    variety VARCHAR(200) NOT NULL DEFAULT '',
    market VARCHAR(200) NOT NULL DEFAULT '',
    state VARCHAR(100) NOT NULL DEFAULT '',
    district VARCHAR(100) NOT NULL DEFAULT '',
    price_date DATE NOT NULL,
    min_price DOUBLE PRECISION,
    max_price DOUBLE PRECISION,
    modal_price DOUBLE PRECISION,
    retail_price DOUBLE PRECISION,
    wholesale_price DOUBLE PRECISION,
    unit VARCHAR(60) NOT NULL DEFAULT '',
    raw_source_reference TEXT,
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_market_price_observation UNIQUE (source, commodity, variety, market, state, district, price_date)
);
CREATE INDEX IF NOT EXISTS idx_market_price_commodity_date ON market_price_observations(commodity, price_date);
CREATE INDEX IF NOT EXISTS idx_market_price_latest ON market_price_observations(source, commodity, price_date DESC);

CREATE TABLE IF NOT EXISTS product_commodity_mappings (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL UNIQUE REFERENCES products(product_id) ON DELETE CASCADE,
    commodity VARCHAR(200) NOT NULL,
    mapping_method VARCHAR(60) NOT NULL DEFAULT 'controlled_rule',
    mapping_reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- 9. FORECASTS (PREDICTED VALUES) TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecasts (
    id BIGSERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES forecast_runs(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_demand DOUBLE PRECISION NOT NULL,
    lower_bound DOUBLE PRECISION,
    upper_bound DOUBLE PRECISION,
    model_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_forecast_run_product_city_date UNIQUE (run_id, product_id, city_name, forecast_date)
);

CREATE INDEX IF NOT EXISTS idx_forecast_product_date ON forecasts(product_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecasts(forecast_date);

-- -----------------------------------------------------------------------------
-- 10. FORECAST EVALUATIONS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS forecast_evaluations (
    id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES forecast_runs(id) ON DELETE CASCADE,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    mae DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    mape DOUBLE PRECISION,
    wape DOUBLE PRECISION,
    evaluation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_eval_run_product ON forecast_evaluations(run_id, product_id);

-- -----------------------------------------------------------------------------
-- 11. INVENTORY STATE TABLE (SIMULATED OR ACTUAL)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    snapshot_date DATE NOT NULL,
    opening_stock DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    stock_received DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    sales_quantity DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    closing_stock DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    is_simulated BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_product_city_date UNIQUE (product_id, city_name, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_inventory_product_date ON inventory(product_id, snapshot_date);

-- -----------------------------------------------------------------------------
-- 12. INVENTORY RECOMMENDATIONS (ROP, EOQ, STOCKOUT ALERTS)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_recommendations (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    calculation_date DATE NOT NULL,
    current_stock DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    avg_daily_demand DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    lead_time_days INTEGER DEFAULT 3 NOT NULL,
    safety_stock DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    reorder_point DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    recommended_order_qty DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    risk_status VARCHAR(50) DEFAULT 'OPTIMAL' NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inv_rec_product_date ON inventory_recommendations(product_id, calculation_date);
CREATE INDEX IF NOT EXISTS idx_inv_rec_risk ON inventory_recommendations(risk_status, priority);

-- -----------------------------------------------------------------------------
-- 13. ANOMALIES TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    product_id BIGINT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    city_name VARCHAR(100) DEFAULT 'ALL' NOT NULL,
    anomaly_date DATE NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'MEDIUM' NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    actual_value DOUBLE PRECISION NOT NULL,
    expected_value DOUBLE PRECISION,
    description TEXT,
    status VARCHAR(50) DEFAULT 'OPEN' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_prod_date ON anomalies(product_id, anomaly_date);
CREATE INDEX IF NOT EXISTS idx_anomaly_status_severity ON anomalies(status, severity);

-- -----------------------------------------------------------------------------
-- 14. CHAT SESSIONS & MESSAGES (RAG ASSISTANT)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    title VARCHAR(255) DEFAULT 'New Chat' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    sender_role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    retrieved_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

-- -----------------------------------------------------------------------------
-- 15. AUDIT LOGS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id VARCHAR(50),
    ip_address VARCHAR(50),
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- -----------------------------------------------------------------------------
-- SEED INITIAL DATA (ROLES AND DEFAULT ADMIN USER)
-- -----------------------------------------------------------------------------
INSERT INTO roles (id, name, description)
VALUES 
    (1, 'admin', 'System Administrator with full management access'),
    (2, 'manager', 'Store and Inventory Manager with operational access'),
    (3, 'viewer', 'Read-only analyst viewer')
ON CONFLICT (name) DO NOTHING;

-- Default Admin User:
-- Username: admin
-- Email: admin@demandintelligence.com
-- Password: Admin@123
INSERT INTO users (id, email, username, hashed_password, full_name, role_id, is_active)
VALUES (
    1,
    'admin@demandintelligence.com',
    'admin',
    '$2b$12$RqQBoi1qlquAZFdEeAdclOwFK5F1X6sfsrwydxlWWShN8iAojItTq',
    'System Administrator',
    1,
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Reset identity sequence for tables with manual IDs seeded
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
