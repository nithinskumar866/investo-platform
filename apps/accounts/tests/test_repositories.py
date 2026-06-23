import pytest
from django.contrib.auth import get_user_model
from apps.accounts.repositories import (
    EntrepreneurProfileRepository,
    InvestorProfileRepository,
    UserRepository,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com",
        password="testpass123",
        role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com",
        password="testpass123",
        role="investor",
    )


class TestUserRepository:
    def test_get_by_email_returns_user(self, db):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        found = UserRepository.get_by_email("test@example.com")
        assert found == user

    def test_get_by_email_case_insensitive(self, db):
        User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        found = UserRepository.get_by_email("Test@Example.COM")
        assert found is not None
        assert found.email == "test@example.com"

    def test_get_by_email_nonexistent(self):
        found = UserRepository.get_by_email("nonexistent@example.com")
        assert found is None

    def test_get_by_id_returns_user(self, db):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        found = UserRepository.get_by_id(user.id)
        assert found == user

    def test_get_by_id_nonexistent(self):
        found = UserRepository.get_by_id(99999)
        assert found is None

    def test_email_exists(self, db):
        User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        assert UserRepository.email_exists("test@example.com") is True
        assert UserRepository.email_exists("other@example.com") is False

    def test_get_active_users(self, db):
        active = User.objects.create_user(
            email="active@example.com",
            password="testpass123",
            is_active=True,
        )
        inactive = User.objects.create_user(
            email="inactive@example.com",
            password="testpass123",
            is_active=False,
        )
        users = UserRepository.get_active_users()
        assert active in users
        assert inactive not in users

    def test_get_users_by_role(self, db):
        ent = User.objects.create_user(
            email="ent@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        inv = User.objects.create_user(
            email="inv@example.com",
            password="testpass123",
            role="investor",
        )
        entrepreneurs = UserRepository.get_users_by_role("entrepreneur")
        assert ent in entrepreneurs
        assert inv not in entrepreneurs


class TestEntrepreneurProfileRepository:
    def test_get_or_create_creates_profile(self, founder):
        profile = EntrepreneurProfileRepository.get_or_create(founder)
        assert profile is not None
        assert profile.user == founder

    def test_get_or_create_returns_existing(self, founder):
        profile1 = EntrepreneurProfileRepository.get_or_create(founder)
        profile2 = EntrepreneurProfileRepository.get_or_create(founder)
        assert profile1.id == profile2.id

    def test_get_by_user_returns_profile(self, founder):
        profile = EntrepreneurProfileRepository.get_by_user(founder)
        assert profile is not None
        assert profile.user == founder

    def test_get_by_user_returns_none_when_no_profile(self, db):
        user = User.objects.create_user(
            email="mentor@example.com",
            password="testpass123",
            role="mentor",
        )
        profile = EntrepreneurProfileRepository.get_by_user(user)
        assert profile is None

    def test_get_public_profiles_filters_public_only(self, founder, db):
        private_user = User.objects.create_user(
            email="private@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        private_user.entrepreneur_profile.is_public = False
        private_user.entrepreneur_profile.save()

        profiles = EntrepreneurProfileRepository.get_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert founder.entrepreneur_profile.id in profile_ids
        assert private_user.entrepreneur_profile.id not in profile_ids

    def test_get_public_profiles_excludes_inactive_users(self, founder, db):
        founder.is_active = False
        founder.save()

        profiles = EntrepreneurProfileRepository.get_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert founder.entrepreneur_profile.id not in profile_ids

    def test_get_profile_completeness_counts_fields(self, founder):
        profile = founder.entrepreneur_profile
        completeness = EntrepreneurProfileRepository.get_profile_completeness(profile)

        assert "total" in completeness
        assert "filled" in completeness
        assert "percentage" in completeness
        assert "missing" in completeness
        assert completeness["total"] == 11
        assert completeness["filled"] == 0
        assert completeness["percentage"] == 0

    def test_get_profile_completeness_with_filled_fields(self, founder):
        profile = founder.entrepreneur_profile
        profile.company_name = "Acme Inc"
        profile.industry = "Tech"
        profile.country = "US"
        profile.city = "San Francisco"
        profile.save()

        completeness = EntrepreneurProfileRepository.get_profile_completeness(profile)
        assert completeness["filled"] >= 4
        assert completeness["percentage"] > 0

    def test_update_profile_updates_fields(self, founder):
        profile = founder.entrepreneur_profile
        updated = EntrepreneurProfileRepository.update_profile(
            profile,
            {"company_name": "NewCo", "tagline": "Innovation"},
        )
        assert updated.company_name == "NewCo"
        assert updated.tagline == "Innovation"

    def test_get_public_profiles_uses_only_deferred_fields(self, founder):
        profiles = EntrepreneurProfileRepository.get_public_profiles()
        profile = profiles.first()
        assert profile is not None
        assert hasattr(profile, "company_name")
        assert hasattr(profile, "user")


class TestInvestorProfileRepository:
    def test_get_or_create_creates_profile(self, investor):
        profile = InvestorProfileRepository.get_or_create(investor)
        assert profile is not None
        assert profile.user == investor

    def test_get_or_create_returns_existing(self, investor):
        profile1 = InvestorProfileRepository.get_or_create(investor)
        profile2 = InvestorProfileRepository.get_or_create(investor)
        assert profile1.id == profile2.id

    def test_get_by_user_returns_profile(self, investor):
        profile = InvestorProfileRepository.get_by_user(investor)
        assert profile is not None
        assert profile.user == investor

    def test_get_by_user_returns_none_when_no_profile(self, db):
        user = User.objects.create_user(
            email="mentor@example.com",
            password="testpass123",
            role="mentor",
        )
        profile = InvestorProfileRepository.get_by_user(user)
        assert profile is None

    def test_get_public_profiles_filters_public_only(self, investor, db):
        private_user = User.objects.create_user(
            email="private@investor.com",
            password="testpass123",
            role="investor",
        )
        private_user.investor_profile.is_public = False
        private_user.investor_profile.save()

        profiles = InvestorProfileRepository.get_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert investor.investor_profile.id in profile_ids
        assert private_user.investor_profile.id not in profile_ids

    def test_get_public_profiles_excludes_inactive_users(self, investor, db):
        investor.is_active = False
        investor.save()

        profiles = InvestorProfileRepository.get_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert investor.investor_profile.id not in profile_ids

    def test_get_investor_statistics_aggregates(self, db):
        for i in range(3):
            user = User.objects.create_user(
                email=f"inv{i}@example.com",
                password="testpass123",
                role="investor",
            )
            user.investor_profile.investor_type = "angel"
            user.investor_profile.ticket_size_min = 50000
            user.investor_profile.ticket_size_max = 500000
            user.investor_profile.years_of_experience = 10
            user.investor_profile.lead_investor = True
            user.investor_profile.save()

        stats = InvestorProfileRepository.get_investor_statistics()
        assert stats["total_investors"] >= 3
        assert stats["by_type"].get("angel", 0) >= 3
        assert stats["lead_investors"] >= 3
        assert stats["avg_ticket_min"] is not None
        assert stats["avg_ticket_max"] is not None
        assert stats["avg_experience"] is not None

    def test_get_investor_statistics_with_no_investors(self):
        stats = InvestorProfileRepository.get_investor_statistics()
        assert stats["total_investors"] == 0
        assert stats["by_type"] == {}
        assert stats["lead_investors"] == 0
        assert stats["avg_ticket_min"] is None
        assert stats["avg_ticket_max"] is None
        assert stats["avg_experience"] is None

    def test_filter_profiles_by_industry(self, investor, db):
        investor.investor_profile.preferred_industries = ["Tech", "AI"]
        investor.investor_profile.save()

        tech_investors = InvestorProfileRepository.filter_profiles(industry="Tech")
        assert investor.investor_profile.id in [p.id for p in tech_investors]

        finance_investors = InvestorProfileRepository.filter_profiles(industry="Finance")
        assert investor.investor_profile.id not in [p.id for p in finance_investors]

    def test_update_profile_updates_fields(self, investor):
        profile = investor.investor_profile
        updated = InvestorProfileRepository.update_profile(
            profile,
            {"bio": "Top tier VC", "city": "New York"},
        )
        assert updated.bio == "Top tier VC"
        assert updated.city == "New York"

    def test_get_profile_completeness_counts_fields(self, investor):
        profile = investor.investor_profile
        completeness = InvestorProfileRepository.get_profile_completeness(profile)
        assert completeness["total"] == 14
        assert completeness["filled"] == 0
        assert completeness["percentage"] == 0
        assert len(completeness["missing"]) == 14
