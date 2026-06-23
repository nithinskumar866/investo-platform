import pytest
from apps.accounts.models import User
from apps.accounts.serializers import (
    RegistrationSerializer,
    UserSerializer,
    TokenObtainSerializer,
    EntrepreneurProfileSerializer,
    InvestorProfileSerializer,
    CompleteUserSerializer,
    PasswordResetConfirmSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PublicEntrepreneurProfileSerializer,
    PublicInvestorProfileSerializer,
    EntrepreneurProfileListSerializer,
    InvestorProfileListSerializer,
    UserUpdateSerializer,
)


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        role="entrepreneur",
    )


@pytest.fixture
def investor_user(db):
    return User.objects.create_user(
        email="investor@example.com",
        password="testpass123",
        role="investor",
        first_name="Alice",
        last_name="Smith",
    )


class TestRegistrationSerializer:
    def test_validates_passwords_match(self, db):
        data = {
            "email": "test@example.com",
            "password": "strongpass123",
            "confirm_password": "differentpass456",
            "first_name": "Test",
            "last_name": "User",
            "role": "entrepreneur",
        }
        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert "confirm_password" in serializer.errors

    def test_validates_password_length(self, db):
        data = {
            "email": "test@example.com",
            "password": "123",
            "confirm_password": "123",
            "first_name": "Test",
            "last_name": "User",
            "role": "entrepreneur",
        }
        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_lowercases_email(self, db):
        data = {
            "email": "  Test@Example.COM  ",
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "Test",
            "last_name": "User",
            "role": "entrepreneur",
        }
        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["email"] == "test@example.com"

    def test_creates_user_with_correct_role(self, db):
        data = {
            "email": "founder@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "entrepreneur",
        }
        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.email == "founder@example.com"
        assert user.role == "entrepreneur"
        assert user.check_password("strongpass123")
        assert user.first_name == "John"
        assert user.last_name == "Doe"

    def test_required_fields(self):
        serializer = RegistrationSerializer(data={})
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "password" in serializer.errors
        assert "confirm_password" in serializer.errors

    def test_password_write_only(self):
        serializer = RegistrationSerializer()
        assert serializer.fields["password"].write_only is True
        assert serializer.fields["confirm_password"].write_only is True


class TestUserSerializer:
    def test_read_only_fields(self, user):
        serializer = UserSerializer(user)
        read_only = {"id", "email", "role", "is_verified", "date_joined"}
        for field in read_only:
            assert serializer.fields[field].read_only is True

    def test_password_not_in_fields(self, user):
        serializer = UserSerializer(user)
        assert "password" not in serializer.fields

    def test_serialization_returns_expected_fields(self, user):
        serializer = UserSerializer(user)
        assert "id" in serializer.data
        assert "email" in serializer.data
        assert "first_name" in serializer.data
        assert "last_name" in serializer.data
        assert "role" in serializer.data
        assert "avatar" in serializer.data
        assert "phone" in serializer.data
        assert "is_verified" in serializer.data
        assert "date_joined" in serializer.data


class TestUserUpdateSerializer:
    def test_allows_update_fields(self):
        serializer = UserUpdateSerializer()
        assert "first_name" in serializer.fields
        assert "last_name" in serializer.fields
        assert "avatar" in serializer.fields
        assert "phone" in serializer.fields

    def test_does_not_include_role_or_email(self):
        serializer = UserUpdateSerializer()
        assert "role" not in serializer.fields
        assert "email" not in serializer.fields
        assert "password" not in serializer.fields


class TestTokenObtainSerializer:
    def test_accepts_email_field_not_username(self):
        serializer = TokenObtainSerializer()
        assert "email" in serializer.fields
        assert "username" not in serializer.fields

    def test_requires_email_and_password(self):
        serializer = TokenObtainSerializer(data={})
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "password" in serializer.errors


class TestPasswordResetConfirmSerializer:
    def test_validates_passwords_match(self):
        data = {
            "email": "test@example.com",
            "otp": "123456",
            "password": "newpass123",
            "confirm_password": "mismatch",
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "confirm_password" in serializer.errors

    def test_valid_passwords_pass(self):
        data = {
            "email": "test@example.com",
            "otp": "123456",
            "password": "newpass123",
            "confirm_password": "newpass123",
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

    def test_min_password_length(self):
        data = {
            "email": "test@example.com",
            "otp": "123456",
            "password": "short",
            "confirm_password": "short",
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "password" in serializer.errors


class TestEntrepreneurProfileSerializer:
    def test_includes_nested_user_data(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
            first_name="John",
            last_name="Doe",
        )
        profile = user.entrepreneur_profile
        serializer = EntrepreneurProfileSerializer(profile)
        assert "user" in serializer.data
        assert serializer.data["user"]["email"] == "founder@example.com"
        assert serializer.data["user"]["first_name"] == "John"
        assert serializer.data["user"]["last_name"] == "Doe"

    def test_read_only_fields(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = user.entrepreneur_profile
        serializer = EntrepreneurProfileSerializer(profile)
        for field in ["id", "user", "created_at", "updated_at"]:
            assert serializer.fields[field].read_only is True


class TestInvestorProfileSerializer:
    def test_includes_nested_user_data(self, investor_user):
        profile = investor_user.investor_profile
        serializer = InvestorProfileSerializer(profile)
        assert "user" in serializer.data
        assert serializer.data["user"]["email"] == "investor@example.com"
        assert serializer.data["user"]["first_name"] == "Alice"

    def test_read_only_fields(self, investor_user):
        profile = investor_user.investor_profile
        serializer = InvestorProfileSerializer(profile)
        for field in ["id", "user", "created_at", "updated_at"]:
            assert serializer.fields[field].read_only is True


class TestCompleteUserSerializer:
    def test_includes_nested_profiles(self, user):
        serializer = CompleteUserSerializer(user)
        assert "entrepreneur_profile" in serializer.data
        assert "investor_profile" in serializer.data
        assert "email" in serializer.data
        assert "role" in serializer.data

    def test_read_only_fields(self, user):
        serializer = CompleteUserSerializer(user)
        for field in ["id", "email", "role", "is_verified", "date_joined"]:
            assert serializer.fields[field].read_only is True


class TestEmailVerificationSerializer:
    def test_requires_email_and_otp(self):
        serializer = EmailVerificationSerializer(data={})
        assert not serializer.is_valid()
        assert "email" in serializer.errors
        assert "otp" in serializer.errors


class TestPasswordResetRequestSerializer:
    def test_requires_email(self):
        serializer = PasswordResetRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_valid_email_passes(self):
        serializer = PasswordResetRequestSerializer(data={"email": "test@example.com"})
        assert serializer.is_valid()


class TestPublicEntrepreneurProfileSerializer:
    def test_hides_sensitive_fields(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = user.entrepreneur_profile
        serializer = PublicEntrepreneurProfileSerializer(profile)
        data = serializer.data
        assert "email" not in data["user"]
        assert "pitch_deck" not in data
        assert "is_public" not in data
        assert "startups" in data
        assert "completeness" in data


class TestPublicInvestorProfileSerializer:
    def test_hides_sensitive_fields(self, investor_user):
        profile = investor_user.investor_profile
        serializer = PublicInvestorProfileSerializer(profile)
        assert "email" not in serializer.data["user"]
        assert "is_public" not in serializer.data

    def test_includes_completeness(self, investor_user):
        profile = investor_user.investor_profile
        serializer = PublicInvestorProfileSerializer(profile)
        assert "completeness" in serializer.data


class TestEntrepreneurProfileListSerializer:
    def test_limited_fields(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = user.entrepreneur_profile
        serializer = EntrepreneurProfileListSerializer(profile)
        fields = {"id", "user", "company_name", "tagline", "industry",
                  "funding_stage", "city", "country", "team_size", "created_at"}
        assert set(serializer.data.keys()) == fields


class TestInvestorProfileListSerializer:
    def test_limited_fields(self, investor_user):
        profile = investor_user.investor_profile
        serializer = InvestorProfileListSerializer(profile)
        fields = {"id", "user", "investor_type", "tagline", "preferred_industries",
                  "preferred_stages", "ticket_size_min", "ticket_size_max",
                  "city", "country", "years_of_experience", "lead_investor",
                  "created_at"}
        assert set(serializer.data.keys()) == fields
