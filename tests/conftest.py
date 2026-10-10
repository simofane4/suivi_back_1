"""Pytest configuration and shared fixtures for all tests."""

import sys
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.test import Client
from rest_framework.test import APIClient, force_authenticate

from cabinets.models import Cabinet, Specialite
from accounts.models import Doctor, Assistant

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup: object, django_db_blocker: object) -> None:
    """Configure Django test database."""
    with django_db_blocker.unblock():
        # Additional database configuration if needed
        pass


@pytest.fixture
def api_client() -> APIClient:
    """Provide a REST API test client."""
    return APIClient()


@pytest.fixture
def django_client() -> Client:
    """Provide a Django test client."""
    return Client()


@pytest.fixture
def specialite(db) -> Specialite:
    """Create a test medical specialty."""
    return Specialite.objects.create(
        name="Médecine Générale",
    )


@pytest.fixture
def cabinet(db) -> Cabinet:
    """Create a test cabinet (clinic) for multi-tenancy testing."""
    return Cabinet.objects.create(
        number="TEST-001",
        name="Test Clinic",
        address="123 Test Street",
    )


@pytest.fixture
def cabinet2(db) -> Cabinet:
    """Create a second test cabinet to test multi-tenancy isolation."""
    return Cabinet.objects.create(
        number="TEST-002",
        name="Test Clinic 2",
        address="456 Test Ave",
    )


@pytest.fixture
def admin_user(db) -> User:
    """Create a superuser admin account."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@test.local",
        password="admin12345",
    )


@pytest.fixture
def doctor_user(db, cabinet: Cabinet, specialite: Specialite) -> User:
    """Create a doctor user account with associated Doctor profile."""
    user = User.objects.create_user(
        username="doctor1",
        email="doctor1@test.local",
        password="doctor12345",
        first_name="Jean",
        last_name="Dupont",
    )
    Doctor.objects.create(
        user=user,
        cabinet=cabinet,
        inp="DR00001",
        gender="Male",
        phone="+212 6 12 34 56 78",
        address="123 Doctor St",
        specialiste=specialite,
    )
    return user


@pytest.fixture
def assistant_user(db, cabinet: Cabinet) -> User:
    """Create an assistant user account with associated Assistant profile."""
    user = User.objects.create_user(
        username="assistant1",
        email="assistant1@test.local",
        password="assistant12345",
        first_name="Marie",
        last_name="Martin",
    )
    Assistant.objects.create(
        user=user,
        cabinet=cabinet,
        cin="SA00001",
        gender="Female",
        phone="+212 6 98 76 54 32",
        address="456 Assistant Ave",
    )
    return user


@pytest.fixture
def doctor2_user(db, cabinet2: Cabinet, specialite: Specialite) -> User:
    """Create a second doctor from a different cabinet."""
    user = User.objects.create_user(
        username="doctor2",
        email="doctor2@test.local",
        password="doctor12345",
        first_name="Pierre",
        last_name="Bernard",
    )
    Doctor.objects.create(
        user=user,
        cabinet=cabinet2,
        inp="DR00002",
        gender="Male",
        phone="+212 6 11 22 33 44",
        address="789 Other St",
        specialiste=specialite,
    )
    return user


@pytest.fixture
def authenticated_client(api_client: APIClient, doctor_user: User) -> APIClient:
    """Return an API client authenticated as a doctor."""
    api_client.force_authenticate(user=doctor_user)
    return api_client


@pytest.fixture
def admin_client(api_client: APIClient, admin_user: User) -> APIClient:
    """Return an API client authenticated as an admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def assistant_client(api_client: APIClient, assistant_user: User) -> APIClient:
    """Return an API client authenticated as an assistant."""
    api_client.force_authenticate(user=assistant_user)
    return api_client


def pytest_configure(config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "django_db: mark test as requiring database access"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
