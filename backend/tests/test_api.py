"""
Comprehensive API Integration Test Suite
Project: Demand-Decision-Intelligence
Location: backend/tests/test_api.py

Covers:
1. Health & OpenApi spec
2. Auth registration, login, and profile (/api/auth/*)
3. Product catalog and categories (/api/products/*)
4. Upload jobs and status (/api/upload/*)
5. Demand daily aggregations (/api/demand/*)
6. Inventory simulation status and recommendations (/api/inventory/*)
7. Analytics trends, pricing elasticity, and anomalies (/api/analytics/*)
8. AI Decision Assistant RAG chat (/api/chat/*)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# Global auth token for protected routes
AUTH_TOKEN = None


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_auth_register_and_login():
    global AUTH_TOKEN
    import uuid
    rand_suffix = str(uuid.uuid4())[:8]
    email = f"analyst_{rand_suffix}@ddi-retail.in"
    username = f"analyst_{rand_suffix}"
    password = "SecurePassword123!"

    # 1. Register
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "full_name": "Senior Retail Analyst"
    })
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == email

    # 2. Login
    login_resp = client.post("/api/auth/login", json={
        "username": email,
        "password": password
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    AUTH_TOKEN = token_data["access_token"]

    # 3. Me profile
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


def test_products_catalog():
    response = client.get("/api/products?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) > 0

    # Test single product
    first_pid = data["products"][0]["product_id"]
    p_resp = client.get(f"/api/products/{first_pid}")
    assert p_resp.status_code == 200
    assert p_resp.json()["product_id"] == first_pid

    # Test categories
    cat_resp = client.get("/api/products/categories")
    assert cat_resp.status_code == 200
    assert "l0_categories" in cat_resp.json()


def test_upload_jobs_list():
    response = client.get("/api/upload/uploads")
    assert response.status_code == 200
    data = response.json()
    assert "uploads" in data
    assert isinstance(data["uploads"], list)


def test_demand_aggregations():
    # Summary
    sum_resp = client.get("/api/demand/summary")
    assert sum_resp.status_code == 200
    assert "total_quantity" in sum_resp.json()

    # Daily series
    daily_resp = client.get("/api/demand/daily?product_id=19512&limit=10")
    assert daily_resp.status_code == 200
    assert "results" in daily_resp.json()


def test_inventory_status_and_recommendations():
    # 1. Simulation status (Closing = Opening + Received - Sales)
    status_resp = client.get("/api/inventory/status?limit=10")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "success"
    assert "data" in status_data
    if status_data["data"]:
        first = status_data["data"][0]
        assert "closing_stock" in first
        assert "days_of_cover" in first
        assert "stockout_risk" in first

    # 2. Recommendations
    rec_resp = client.get("/api/inventory/recommendations?limit=10")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["status"] == "success"
    assert "data" in rec_data


def test_analytics_trends_and_pricing():
    # 1. Trends
    trends_resp = client.get("/api/analytics/trends")
    assert trends_resp.status_code == 200
    t_data = trends_resp.json()
    assert "wow_growth_volume_pct" in t_data
    assert "category_growth" in t_data

    # 2. Pricing elasticity
    pricing_resp = client.get("/api/analytics/pricing")
    assert pricing_resp.status_code == 200
    p_data = pricing_resp.json()
    assert "categories" in p_data
    assert "overall_discount_correlation" in p_data

    # 3. Anomalies
    anom_resp = client.get("/api/analytics/anomalies?limit=10&severity=ALL")
    assert anom_resp.status_code == 200
    assert "alerts" in anom_resp.json()


def test_ai_decision_assistant_chat():
    # 1. Stockout Risk Query
    msg_resp = client.post("/api/chat/message", json={
        "message": "Which products are at risk of stockout next week?"
    })
    assert msg_resp.status_code == 200
    data = msg_resp.json()
    assert "session_id" in data
    assert "message" in data
    assert data["role"] == "assistant"
    assert "citations" in data
    session_id = data["session_id"]

    # 2. History verification
    hist_resp = client.get(f"/api/chat/history?session_id={session_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["session_id"] == session_id
    assert len(hist_data["messages"]) >= 2

    # 3. List sessions
    sess_resp = client.get("/api/chat/sessions")
    assert sess_resp.status_code == 200
    assert "sessions" in sess_resp.json()
