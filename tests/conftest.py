import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    return TestClient(app)


@pytest.fixture
def admin_headers():
    """Заголовки для администратора"""
    return {"X-User-Id": "1", "X-User-Role": "admin"}


@pytest.fixture
def user_headers():
    """Заголовки для обычного пользователя"""
    return {"X-User-Id": "2", "X-User-Role": "student"}


@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword2",
        "role": "student",
    }


@pytest.fixture
def test_asset_data():
    return {"title": "Test Asset", "inv_id": "TEST_INV_ID"}


@pytest.fixture
def test_checkout_data():
    from datetime import datetime, timedelta

    return {
        "asset_id": 1,
        "due_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "status": "active",
    }
