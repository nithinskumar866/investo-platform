import pytest
from apps.accounts.models import User, EntrepreneurProfile, InvestorProfile


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        role="entrepreneur",
    )


class TestUserModel:
    def test_create_user_with_different_roles(self, db):
        roles = ["entrepreneur", "investor", "mentor", "talent", "admin"]
        for role in roles:
            user = User.objects.create_user(
                email=f"{role}@example.com",
                password="testpass123",
                role=role,
            )
            assert user.role == role

    def test_user_str_returns_email(self, db):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        assert str(user) == "test@example.com"

    def test_entrepreneur_profile_cascades_from_user(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        assert hasattr(user, "entrepreneur_profile")
        assert isinstance(user.entrepreneur_profile, EntrepreneurProfile)

    def test_investor_profile_cascades_from_user(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        assert hasattr(user, "investor_profile")
        assert isinstance(user.investor_profile, InvestorProfile)

    def test_entrepreneur_profile_str_format(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = user.entrepreneur_profile
        expected = f"{profile.company_name or user.email} ({user.email})"
        assert str(profile) == expected

    def test_investor_profile_str_format(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        profile = user.investor_profile
        assert str(profile) == f"Investor {user.email} ({profile.investor_type or 'no type'})"

    def test_email_normalized_by_manager(self, db):
        user = User.objects.create_user(
            email="Test@Example.COM",
            password="testpass123",
        )
        assert user.email == "Test@example.com"

    def test_is_verified_default_false(self, db):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        assert user.is_verified is False

    def test_role_enum_values_match(self):
        assert User.Role.ENTREPRENEUR == "entrepreneur"
        assert User.Role.INVESTOR == "investor"
        assert User.Role.MENTOR == "mentor"
        assert User.Role.TALENT == "talent"
        assert User.Role.ADMIN == "admin"


class TestEntrepreneurProfileModel:
    def test_no_profile_for_non_entrepreneur(self, db):
        user = User.objects.create_user(
            email="talent@example.com",
            password="testpass123",
            role="talent",
        )
        assert not hasattr(user, "entrepreneur_profile")

    def test_profile_on_delete_user_cascades(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile_id = user.entrepreneur_profile.id
        user.delete()
        assert EntrepreneurProfile.objects.filter(id=profile_id).count() == 0


class TestInvestorProfileModel:
    def test_no_profile_for_non_investor(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        assert not hasattr(user, "investor_profile")

    def test_profile_on_delete_user_cascades(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        profile_id = user.investor_profile.id
        user.delete()
        assert InvestorProfile.objects.filter(id=profile_id).count() == 0
