import pytest


@pytest.fixture
def user(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="test@example.com", password="testpass123", role="entrepreneur"
    )


@pytest.fixture
def founder(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur"
    )


@pytest.fixture
def investor(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor"
    )


@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User
    return User.objects.create_user(
        email="admin@example.com", password="testpass123", role="admin"
    )


@pytest.fixture
def startup(db, user):
    from apps.startups.models import Startup
    return Startup.objects.create(
        owner=user,
        name="Test Startup",
        industry="saas",
        stage="seed",
        status="active",
        is_visible=True,
    )


@pytest.fixture
def draft_startup(db, user):
    from apps.startups.models import Startup
    return Startup.objects.create(
        owner=user,
        name="Draft Startup",
        industry="fintech",
        stage="idea",
        status="draft",
        is_visible=False,
    )
