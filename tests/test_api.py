"""
Tests for the Inventory Manager API.

Run with:  pytest tests/ -v
Requires:  DATABASE_URL set to a test SQLite file (see conftest.py)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Register a user and return Authorization headers."""
    await client.post("/auth/register", json={"username": "testuser", "password": "securepass123"})
    resp = await client.post("/auth/login", json={"username": "testuser", "password": "securepass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    resp = await client.post("/auth/register", json={"username": "newuser", "password": "password123"})
    assert resp.status_code == 201
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/auth/register", json={"username": "dupuser", "password": "password123"})
    resp = await client.post("/auth/register", json={"username": "dupuser", "password": "password123"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={"username": "logintest", "password": "correct123"})
    resp = await client.post("/auth/login", json={"username": "logintest", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient):
    resp = await client.get("/products/")
    assert resp.status_code == 401


# ── Products ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/products/",
        json={"name": "Widget", "price": 9.99, "sku": "WGT-001", "quantity": 50},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Widget"
    assert data["sku"] == "WGT-001"
    assert data["is_low_stock"] is False


@pytest.mark.asyncio
async def test_duplicate_sku(client: AsyncClient, auth_headers):
    payload = {"name": "Item A", "price": 1.0, "sku": "DUPE-001", "quantity": 5}
    await client.post("/products/", json=payload, headers=auth_headers)
    resp = await client.post("/products/", json=payload, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_products_pagination(client: AsyncClient, auth_headers):
    for i in range(5):
        await client.post(
            "/products/",
            json={"name": f"Product {i}", "price": float(i), "sku": f"PAG-{i:03d}", "quantity": i * 5},
            headers=auth_headers,
        )
    resp = await client.get("/products/?page=1&page_size=3", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 3
    assert "total" in data
    assert "pages" in data


@pytest.mark.asyncio
async def test_search_products(client: AsyncClient, auth_headers):
    await client.post(
        "/products/",
        json={"name": "Blue Widget", "price": 5.0, "sku": "BLUE-001", "quantity": 10},
        headers=auth_headers,
    )
    resp = await client.get("/products/?search=Blue", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Blue" in p["name"] for p in items)


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, auth_headers):
    create = await client.post(
        "/products/",
        json={"name": "Old Name", "price": 1.0, "sku": "UPD-001", "quantity": 10},
        headers=auth_headers,
    )
    pid = create.json()["id"]
    resp = await client.put(f"/products/{pid}", json={"name": "New Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, auth_headers):
    create = await client.post(
        "/products/",
        json={"name": "To Delete", "price": 1.0, "sku": "DEL-001", "quantity": 1},
        headers=auth_headers,
    )
    pid = create.json()["id"]
    resp = await client.delete(f"/products/{pid}", headers=auth_headers)
    assert resp.status_code == 204
    resp = await client.get(f"/products/{pid}", headers=auth_headers)
    assert resp.status_code == 404


# ── Stock ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_low_stock_alert(client: AsyncClient, auth_headers):
    await client.post(
        "/products/",
        json={"name": "Low Stock Item", "price": 2.0, "sku": "LOW-001",
              "quantity": 3, "low_stock_threshold": 10},
        headers=auth_headers,
    )
    resp = await client.get("/products/low-stock", headers=auth_headers)
    assert resp.status_code == 200
    skus = [p["sku"] for p in resp.json()]
    assert "LOW-001" in skus


@pytest.mark.asyncio
async def test_adjust_stock(client: AsyncClient, auth_headers):
    create = await client.post(
        "/products/",
        json={"name": "Stock Item", "price": 3.0, "sku": "STK-001", "quantity": 20},
        headers=auth_headers,
    )
    pid = create.json()["id"]
    resp = await client.patch(f"/products/{pid}/stock?delta=30", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 50


@pytest.mark.asyncio
async def test_adjust_stock_below_zero(client: AsyncClient, auth_headers):
    create = await client.post(
        "/products/",
        json={"name": "Small Stock", "price": 1.0, "sku": "SS-001", "quantity": 5},
        headers=auth_headers,
    )
    pid = create.json()["id"]
    resp = await client.patch(f"/products/{pid}/stock?delta=-100", headers=auth_headers)
    assert resp.status_code == 400


# ── Categories ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_categories(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/categories/",
        json={"name": "Electronics", "description": "Electronic goods"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    resp = await client.get("/categories/", headers=auth_headers)
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Electronics" in names


@pytest.mark.asyncio
async def test_product_with_category(client: AsyncClient, auth_headers):
    cat = await client.post("/categories/", json={"name": "Tools"}, headers=auth_headers)
    cat_id = cat.json()["id"]
    resp = await client.post(
        "/products/",
        json={"name": "Hammer", "price": 14.99, "sku": "TOOL-001",
              "quantity": 30, "category_id": cat_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["category"]["name"] == "Tools"
