"""
pytest root configuration for Investo.

This conftest provides:
- Django setup via pytest-django (DJANGO_SETTINGS_MODULE in pyproject.toml)
- Reusable fixtures for all test modules
- Authenticated API client fixtures for every user role
- Test helpers for JWT token generation
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture(autouse=True)
def enable_db_access(db):
    """Enable database access globally for all tests in pytest-django."""
    pass


# ── Fixture: API Client ────────────────────────────────────────────

@pytest.fixture
def api_client():
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an APIClient authenticated as `user` with JWT tokens."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["email"] = user.email
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def founder_client(api_client, founder):
    """Return an APIClient authenticated as a founder user."""
    refresh = RefreshToken.for_user(founder)
    refresh["role"] = founder.role
    refresh["email"] = founder.email
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def investor_client(api_client, investor):
    """Return an APIClient authenticated as an investor user."""
    refresh = RefreshToken.for_user(investor)
    refresh["role"] = investor.role
    refresh["email"] = investor.email
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return an APIClient authenticated as an admin user."""
    refresh = RefreshToken.for_user(admin_user)
    refresh["role"] = admin_user.role
    refresh["email"] = admin_user.email
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client


# ── Auth Helper Functions ──────────────────────────────────────────

def get_tokens_for_user(user):
    """Generate JWT access + refresh tokens for a given user."""
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["email"] = user.email
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def auth_header(user):
    """Return HTTP Authorization header dict for a user."""
    tokens = get_tokens_for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}


# ── Response Assertion Helpers ─────────────────────────────────────

def assert_success_response(response, status_code=200):
    """Assert that a response has a success status and wrapped format."""
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.content}"
    )
    data = response.json()
    if "status" in data and data["status"] != "success":
        pytest.fail(f"Response status is not success: {data}")


def assert_error_response(response, status_code=400, error_code=None):
    """Assert that a response has an error status and optionally a specific error code."""
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.content}"
    )
    data = response.json()
    assert data.get("status") == "error", f"Response is not an error: {data}"
    if error_code:
        assert data.get("error", {}).get("code") == error_code, (
            f"Expected error code {error_code}, got {data.get('error', {})}"
        )


def get_data(response):
    """Extract the `data` key from a wrapped response."""
    return response.json().get("data", response.json())
