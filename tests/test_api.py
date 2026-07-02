"""
Tests for the Hostel Asset Management API.

Run with:  pytest tests/ -v
Requires:  DATABASE_URL set to a test SQLite file (see conftest.py, if added)
"""
from app.core.database import prisma
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid

from main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client():
    await prisma.connect()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    await prisma.disconnect()

@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Register a user and return Authorization headers.

    NOTE: /auth/login expects form-encoded data (OAuth2PasswordRequestForm),
    not JSON — that's why this uses `data=` instead of `json=`.
    """
    await client.post("/auth/register", json={"username": "testuser", "password": "securepass123"})
    resp = await client.post("/auth/login", data={"username": "testuser", "password": "securepass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def hostel_id(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/hostels/",
        json={"name": "Test Hostel"},
        headers=auth_headers,
    )

    print(resp.status_code)
    print(resp.json())

    return resp.json()["id"]

@pytest_asyncio.fixture
async def room_id(client: AsyncClient, auth_headers, hostel_id):
    """Creates a room inside the hostel fixture so asset tests have a valid parent."""
    resp = await client.post(
        "/rooms/",
        json={"room_number": "101", "floor": 1, "capacity": 2, "hostel_id": hostel_id},
        headers=auth_headers,
    )
    return resp.json()["id"]


# ── Auth ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    username = f"user_{uuid.uuid4().hex[:8]}"
    resp = await client.post(
    "/auth/register",
    json={
        "username": username,
        "password": "password123",
    },
)


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await client.post("/auth/register", json={"username": "dupuser", "password": "password123"})
    resp = await client.post("/auth/register", json={"username": "dupuser", "password": "password123"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={"username": "logintest", "password": "correct123"})
    resp = await client.post("/auth/login", data={"username": "logintest", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_requires_auth(client: AsyncClient):
    resp = await client.get("/hostels/")
    assert resp.status_code == 401


# ── Assets ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_asset(client: AsyncClient, auth_headers, room_id):
    resp = await client.post(
        "/assets/",
        json={"name": "Study Table", "asset_type": "Furniture", "quantity": 2, "room_id": room_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Study Table"
    assert data["condition"] == "Good"  # default value


@pytest.mark.asyncio
async def test_list_assets_pagination(client: AsyncClient, auth_headers, room_id):
    for i in range(5):
        await client.post(
            "/assets/",
            json={"name": f"Chair {i}", "asset_type": "Furniture", "quantity": i, "room_id": room_id},
            headers=auth_headers,
        )
    resp = await client.get("/assets/?page=1&page_size=3", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 3
    assert "total" in data
    assert "pages" in data


@pytest.mark.asyncio
async def test_search_assets(client: AsyncClient, auth_headers, room_id):
    await client.post(
        "/assets/",
        json={"name": "Blue Mattress", "asset_type": "Bedding", "quantity": 1, "room_id": room_id},
        headers=auth_headers,
    )
    resp = await client.get("/assets/?search=Blue", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Blue" in a["name"] for a in items)


@pytest.mark.asyncio
async def test_update_asset(client: AsyncClient, auth_headers, room_id):
    create = await client.post(
        "/assets/",
        json={"name": "Old Fan", "asset_type": "Electronics", "quantity": 1, "room_id": room_id},
        headers=auth_headers,
    )
    aid = create.json()["id"]
    resp = await client.put(f"/assets/{aid}", json={"name": "New Fan"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Fan"


@pytest.mark.asyncio
async def test_delete_asset(client: AsyncClient, auth_headers, room_id):
    create = await client.post(
        "/assets/",
        json={"name": "To Delete", "asset_type": "Misc", "quantity": 1, "room_id": room_id},
        headers=auth_headers,
    )
    aid = create.json()["id"]
    resp = await client.delete(f"/assets/{aid}", headers=auth_headers)
    assert resp.status_code == 204
    resp = await client.get(f"/assets/{aid}", headers=auth_headers)
    assert resp.status_code == 404


# ── Quantity adjustment ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_adjust_quantity(client: AsyncClient, auth_headers, room_id):
    create = await client.post(
        "/assets/",
        json={"name": "Bucket", "asset_type": "Misc", "quantity": 20, "room_id": room_id},
        headers=auth_headers,
    )
    aid = create.json()["id"]
    resp = await client.patch(f"/assets/{aid}/quantity?delta=30", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["quantity"] == 50


@pytest.mark.asyncio
async def test_adjust_quantity_below_zero(client: AsyncClient, auth_headers, room_id):
    create = await client.post(
        "/assets/",
        json={"name": "Small Stock Item", "asset_type": "Misc", "quantity": 5, "room_id": room_id},
        headers=auth_headers,
    )
    aid = create.json()["id"]
    resp = await client.patch(f"/assets/{aid}/quantity?delta=-100", headers=auth_headers)
    assert resp.status_code == 400


# ── Rooms ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_room_number_same_hostel(client: AsyncClient, auth_headers, hostel_id):
    payload = {"room_number": "303", "floor": 3, "capacity": 2, "hostel_id": hostel_id}
    await client.post("/rooms/", json=payload, headers=auth_headers)
    resp = await client.post("/rooms/", json=payload, headers=auth_headers)
    assert resp.status_code == 400


# ── Hostels ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_hostels(client: AsyncClient, auth_headers):
    resp = await client.post("/hostels/", json={"name": "Green Block"}, headers=auth_headers)
    assert resp.status_code == 201
    resp = await client.get("/hostels/", headers=auth_headers)
    assert resp.status_code == 200
    names = [h["name"] for h in resp.json()]
    assert "Green Block" in names