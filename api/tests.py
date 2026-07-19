"""
Tests for the Hostel Asset Management API (Django REST Framework version).

Run with:  pytest -v
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Hostel, Room, Asset

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide an API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )


@pytest.fixture
def auth_client(api_client, user):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def hostel(db):
    """Create a test hostel."""
    return Hostel.objects.create(
        name='Test Hostel',
        description='A test hostel'
    )


@pytest.fixture
def room(db, hostel):
    """Create a test room."""
    return Room.objects.create(
        room_number='101',
        floor=1,
        capacity=2,
        hostel=hostel
    )


@pytest.fixture
def asset(db, room):
    """Create a test asset."""
    return Asset.objects.create(
        name='Study Table',
        asset_type='Furniture',
        condition='Good',
        quantity=2,
        room=room
    )


# ──────── Authentication Tests ────────────────────────────────────────────────


@pytest.mark.django_db
class TestAuth:
    def test_register_success(self, api_client):
        """Test user registration."""
        response = api_client.post('/api/auth/register', {
            'username': 'newuser',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'email': 'new@example.com'
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['user']['username'] == 'newuser'

    def test_register_password_mismatch(self, api_client):
        """Test registration fails with mismatched passwords."""
        response = api_client.post('/api/auth/register', {
            'username': 'newuser',
            'password': 'securepass123',
            'password_confirm': 'wrongpass456',
            'email': 'new@example.com'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self, api_client, user):
        """Test registration fails with duplicate username."""
        response = api_client.post('/api/auth/register', {
            'username': 'testuser',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'email': 'another@example.com'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_success(self, api_client, user):
        """Test user login."""
        response = api_client.post('/api/auth/login', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert data['user']['username'] == 'testuser'

    def test_login_invalid_credentials(self, api_client, user):
        """Test login fails with invalid credentials."""
        response = api_client.post('/api/auth/login', {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_protected_route_requires_auth(self, api_client):
        """Test that protected routes require authentication."""
        response = api_client.get('/api/hostels/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ──────── Hostel Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHostels:
    def test_create_hostel(self, auth_client):
        """Test creating a hostel."""
        response = auth_client.post('/api/hostels/', {
            'name': 'New Hostel',
            'description': 'A brand new hostel'
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == 'New Hostel'
        assert data['rooms_count'] == 0

    def test_create_duplicate_hostel(self, auth_client, hostel):
        """Test creating a hostel with duplicate name fails."""
        response = auth_client.post('/api/hostels/', {
            'name': 'Test Hostel',
            'description': 'Another hostel'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_hostels(self, auth_client, hostel):
        """Test listing hostels."""
        response = auth_client.get('/api/hostels/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'results' in data or isinstance(data, list)

    def test_retrieve_hostel(self, auth_client, hostel):
        """Test retrieving a single hostel."""
        response = auth_client.get(f'/api/hostels/{hostel.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Test Hostel'

    def test_delete_hostel(self, auth_client, hostel):
        """Test deleting a hostel cascades to rooms and assets."""
        hostel_id = hostel.id
        response = auth_client.delete(f'/api/hostels/{hostel_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Hostel.objects.filter(id=hostel_id).exists()


# ──────── Room Tests ──────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRooms:
    def test_create_room(self, auth_client, hostel):
        """Test creating a room."""
        response = auth_client.post('/api/rooms/', {
            'room_number': '201',
            'floor': 2,
            'capacity': 3,
            'hostel': hostel.id
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['room_number'] == '201'

    def test_duplicate_room_number_same_hostel(self, auth_client, room):
        """Test duplicate room number in same hostel is rejected."""
        response = auth_client.post('/api/rooms/', {
            'room_number': '101',
            'floor': 1,
            'capacity': 2,
            'hostel': room.hostel.id
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_room_number_different_hostel_allowed(self, auth_client, hostel, room):
        """Test same room number is allowed in different hostels."""
        hostel2 = Hostel.objects.create(name='Other Hostel')
        response = auth_client.post('/api/rooms/', {
            'room_number': '101',
            'floor': 1,
            'capacity': 2,
            'hostel': hostel2.id
        })
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_rooms(self, auth_client, room):
        """Test listing rooms."""
        response = auth_client.get('/api/rooms/')
        assert response.status_code == status.HTTP_200_OK

    def test_search_rooms(self, auth_client, room):
        """Test searching rooms."""
        response = auth_client.get(f'/api/rooms/?search={room.room_number}')
        assert response.status_code == status.HTTP_200_OK

    def test_delete_room_cascades(self, auth_client, room, asset):
        """Test deleting a room cascades to assets."""
        room_id = room.id
        asset_id = asset.id
        response = auth_client.delete(f'/api/rooms/{room_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Room.objects.filter(id=room_id).exists()
        assert not Asset.objects.filter(id=asset_id).exists()


# ──────── Asset Tests ────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAssets:
    def test_create_asset(self, auth_client, room):
        """Test creating an asset."""
        response = auth_client.post('/api/assets/', {
            'name': 'Bed',
            'asset_type': 'Furniture',
            'condition': 'Good',
            'quantity': 1,
            'room': room.id
        })
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data['name'] == 'Bed'
        assert data['condition'] == 'Good'

    def test_list_assets_paginated(self, auth_client, room):
        """Test listing assets with pagination."""
        # Create multiple assets
        for i in range(15):
            Asset.objects.create(
                name=f'Chair {i}',
                asset_type='Furniture',
                quantity=1,
                room=room
            )
        response = auth_client.get('/api/assets/?page=1')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'results' in data
        assert len(data['results']) <= 10  # Default page size

    def test_search_assets(self, auth_client, room):
        """Test searching assets."""
        Asset.objects.create(
            name='Blue Mattress',
            asset_type='Bedding',
            quantity=1,
            room=room
        )
        response = auth_client.get('/api/assets/?search=Blue')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        results = data.get('results', [])
        assert any('Blue' in a['name'] for a in results)

    def test_retrieve_asset(self, auth_client, asset):
        """Test retrieving a single asset."""
        response = auth_client.get(f'/api/assets/{asset.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Study Table'

    def test_update_asset(self, auth_client, asset):
        """Test updating an asset."""
        response = auth_client.put(f'/api/assets/{asset.id}/', {
            'name': 'Updated Table',
            'asset_type': 'Furniture',
            'condition': 'Fair',
            'quantity': 3,
            'room': asset.room.id
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['name'] == 'Updated Table'
        assert data['condition'] == 'Fair'

    def test_partial_update_asset(self, auth_client, asset):
        """Test partially updating an asset."""
        response = auth_client.patch(f'/api/assets/{asset.id}/', {
            'condition': 'Poor'
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['condition'] == 'Poor'
        assert data['name'] == 'Study Table'  # Unchanged

    def test_adjust_quantity_increment(self, auth_client, asset):
        """Test adjusting asset quantity (increment)."""
        response = auth_client.patch(f'/api/assets/{asset.id}/quantity/', {
            'quantity': 5
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['quantity'] == 7  # 2 + 5

    def test_adjust_quantity_decrement(self, auth_client, asset):
        """Test adjusting asset quantity (decrement)."""
        response = auth_client.patch(f'/api/assets/{asset.id}/quantity/', {
            'quantity': -1
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['quantity'] == 1  # 2 - 1

    def test_adjust_quantity_prevents_negative(self, auth_client, asset):
        """Test that quantity adjustment prevents negative values."""
        response = auth_client.patch(f'/api/assets/{asset.id}/quantity/', {
            'quantity': -100
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['quantity'] == 0  # Clamped to 0

    def test_delete_asset(self, auth_client, asset):
        """Test deleting an asset."""
        asset_id = asset.id
        response = auth_client.delete(f'/api/assets/{asset_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Asset.objects.filter(id=asset_id).exists()

    def test_list_asset_by_condition(self, auth_client, room):
        """Test filtering assets by condition."""
        Asset.objects.create(name='Good Item', asset_type='Test', condition='Good', quantity=1, room=room)
        Asset.objects.create(name='Poor Item', asset_type='Test', condition='Poor', quantity=1, room=room)
        response = auth_client.get('/api/assets/?search=Poor')
        assert response.status_code == status.HTTP_200_OK
