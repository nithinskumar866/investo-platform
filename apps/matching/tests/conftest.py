import pytest
from decimal import Decimal

from apps.accounts.models import User, InvestorProfile
from apps.startups.models import Startup

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(
        email="testuser@example.com",
        password="password123",
        role="mentor",
    )


@pytest.fixture
def founder():
    return User.objects.create_user(
        email="founder@example.com",
        password="password123",
        first_name="Jane",
        last_name="Founder",
        role="entrepreneur",
    )


@pytest.fixture
def investor():
    u = User.objects.create_user(
        email="investor@example.com",
        password="password123",
        first_name="John",
        last_name="Investor",
        role="investor",
    )
    profile, _ = InvestorProfile.objects.get_or_create(user=u)
    profile.investor_type = "angel"
    profile.bio = "Active angel investor"
    profile.tagline = "Looking for startups"
    profile.investment_focus = "AI ML SaaS"
    profile.preferred_industries = ["ai_ml", "saas"]
    profile.preferred_stages = ["seed", "series_a"]
    profile.ticket_size_min = Decimal("100000")
    profile.ticket_size_max = Decimal("1000000")
    profile.save()
    return u


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        password="password123",
        role="admin",
        is_staff=True,
    )


@pytest.fixture
def startup(founder):
    return Startup.objects.create(
        owner=founder,
        name="Test Startup",
        slug="test-startup",
        tagline="Innovative test startup",
        short_description="A short description",
        description="A much longer description of this startup",
        industry="ai_ml",
        stage="seed",
        funding_goal=Decimal("500000"),
        location="San Francisco, CA",
        website="https://teststartup.com",
        is_visible=True,
        status="active",
    )


@pytest.fixture
def investor_preference(investor):
    from apps.matching.models import InvestorPreference
    return InvestorPreference.objects.create(
        user=investor,
        preferred_industries=["ai_ml", "saas"],
        preferred_stages=["seed", "series_a"],
        min_ticket_size=Decimal("100000"),
        max_ticket_size=Decimal("1000000"),
        preferred_geographies=["United States"],
        risk_appetite=InvestorPreference.RiskAppetite.MODERATE,
        investment_focus="AI ML SaaS",
        is_active=True,
    )


@pytest.fixture
def match_score(investor, startup):
    from apps.matching.models import MatchScore
    return MatchScore.objects.create(
        investor=investor,
        startup=startup,
        score=Decimal("85.50"),
        score_breakdown={
            "industry": 30.0, "stage": 15.0, "funding": 12.5,
            "geography": 10.0, "keywords": 8.0,
            "startup_completeness": 4.0, "investor_completeness": 3.0,
            "startup_activity": 2.0, "investor_activity": 1.0,
        },
        status=MatchScore.Status.RECOMMENDED,
    )
