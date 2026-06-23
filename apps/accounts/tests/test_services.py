import pytest
from unittest.mock import patch, MagicMock
from django.core.cache import cache
from django.contrib.auth import get_user_model
from apps.accounts.services import AuthService, EntrepreneurProfileService, InvestorProfileService

User = get_user_model()


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
    )


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


class TestAuthServiceGenerateOtp:
    def test_returns_six_digit_string(self):
        otp = AuthService._generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_values_are_in_range(self):
        for _ in range(100):
            otp = int(AuthService._generate_otp())
            assert 100000 <= otp <= 999999


class TestAuthServiceHashOtp:
    def test_returns_sha256_hex_string(self):
        otp = "123456"
        hashed = AuthService._hash_otp(otp)
        assert len(hashed) == 64
        assert hashed.isalnum()

    def test_same_input_produces_same_hash(self):
        assert AuthService._hash_otp("123456") == AuthService._hash_otp("123456")

    def test_different_input_produces_different_hash(self):
        assert AuthService._hash_otp("123456") != AuthService._hash_otp("654321")


class TestAuthServiceSendVerificationEmail:
    @patch("apps.accounts.services.EmailService.send_verification")
    def test_stores_otp_hash_in_cache(self, mock_send_verification, user):
        cache_key = f"otp:verify:{user.email}"
        cache.delete(cache_key)

        otp = AuthService.send_verification_email(user)

        stored_hash = cache.get(cache_key)
        assert stored_hash is not None
        assert stored_hash == AuthService._hash_otp(otp)

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_sends_email_with_correct_params(self, mock_send_verification, user):
        otp = AuthService.send_verification_email(user)

        mock_send_verification.assert_called_once_with(
            recipient_email=user.email,
            recipient_name=user.email,
            otp=otp,
        )

    @patch("apps.accounts.services.cache")
    @patch("apps.accounts.services.EmailService.send_verification")
    def test_otp_has_600_second_ttl(self, mock_send_verification, mock_cache, user):
        AuthService.send_verification_email(user)
        mock_cache.set.assert_called_once()
        _, kwargs = mock_cache.set.call_args
        assert kwargs.get("timeout") == 600

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_returns_plaintext_otp(self, mock_send_verification, user):
        otp = AuthService.send_verification_email(user)

        assert len(otp) == 6
        assert otp.isdigit()


class TestAuthServiceVerifyEmail:
    @patch("apps.accounts.services.EmailService.send_verification")
    def test_valid_otp_marks_user_verified(self, mock_send, user, db):
        otp = AuthService.send_verification_email(user)

        result = AuthService.verify_email(email=user.email, otp=otp)

        assert result is True
        user.refresh_from_db()
        assert user.is_verified is True
        assert user.email_verified_at is not None

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_valid_otp_deletes_cache(self, mock_send, user, db):
        otp = AuthService.send_verification_email(user)
        cache_key = f"otp:verify:{user.email}"

        AuthService.verify_email(email=user.email, otp=otp)

        assert cache.get(cache_key) is None

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_invalid_otp_returns_false(self, mock_send, user, db):
        AuthService.send_verification_email(user)

        result = AuthService.verify_email(email=user.email, otp="000000")

        assert result is False
        user.refresh_from_db()
        assert user.is_verified is False

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_expired_otp_returns_false(self, mock_send, user, db):
        cache_key = f"otp:verify:{user.email}"
        cache.delete(cache_key)

        result = AuthService.verify_email(email=user.email, otp="123456")

        assert result is False
        user.refresh_from_db()
        assert user.is_verified is False

    @patch("apps.accounts.services.EmailService.send_verification")
    def test_nonexistent_user_returns_false(self, mock_send, user, db):
        otp = AuthService.send_verification_email(user)

        result = AuthService.verify_email(email="nonexistent@example.com", otp=otp)

        assert result is False


class TestAuthServiceSendPasswordResetOtp:
    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_stores_otp_hash_in_cache(self, mock_send_reset, user, db):
        cache_key = f"otp:reset:{user.email}"
        cache.delete(cache_key)

        otp = AuthService.send_password_reset_otp(user.email)

        stored_hash = cache.get(cache_key)
        assert stored_hash is not None
        assert stored_hash == AuthService._hash_otp(otp)

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_sends_email_with_correct_params(self, mock_send_reset, user, db):
        otp = AuthService.send_password_reset_otp(user.email)

        mock_send_reset.assert_called_once_with(
            recipient_email=user.email,
            otp=otp,
        )

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_returns_empty_string_for_nonexistent_email(self, mock_send_reset, db):
        result = AuthService.send_password_reset_otp("nonexistent@example.com")

        assert result == ""
        mock_send_reset.assert_not_called()


class TestAuthServiceResetPassword:
    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_valid_otp_changes_password(self, mock_send, user, db):
        old_password = user.password
        otp = AuthService.send_password_reset_otp(user.email)

        result = AuthService.reset_password(
            email=user.email,
            otp=otp,
            new_password="newstrongpass456",
        )

        assert result is True
        user.refresh_from_db()
        assert user.password != old_password
        assert user.check_password("newstrongpass456")

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_valid_otp_deletes_cache(self, mock_send, user, db):
        cache_key = f"otp:reset:{user.email}"
        otp = AuthService.send_password_reset_otp(user.email)

        AuthService.reset_password(
            email=user.email,
            otp=otp,
            new_password="newstrongpass456",
        )

        assert cache.get(cache_key) is None

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_invalid_otp_returns_false(self, mock_send, user, db):
        AuthService.send_password_reset_otp(user.email)

        result = AuthService.reset_password(
            email=user.email,
            otp="000000",
            new_password="newstrongpass456",
        )

        assert result is False

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_expired_otp_returns_false(self, mock_send, user, db):
        cache_key = f"otp:reset:{user.email}"
        cache.delete(cache_key)

        result = AuthService.reset_password(
            email=user.email,
            otp="123456",
            new_password="newstrongpass456",
        )

        assert result is False

    @patch("apps.accounts.services.EmailService.send_password_reset")
    def test_nonexistent_user_returns_false(self, mock_send, user, db):
        cache_key = f"otp:reset:nonexistent@example.com"
        otp_hash = AuthService._hash_otp("123456")
        cache.set(cache_key, otp_hash, timeout=600)

        result = AuthService.reset_password(
            email="nonexistent@example.com",
            otp="123456",
            new_password="newstrongpass456",
        )

        assert result is False


class TestAuthServiceSendWelcomeEmail:
    @patch("apps.accounts.services.EmailService.send_welcome")
    def test_sends_welcome_email(self, mock_send_welcome, user):
        AuthService.send_welcome_email(user)

        mock_send_welcome.assert_called_once_with(
            recipient_email=user.email,
            recipient_name=user.email,
            dashboard_url="http://localhost:3000/dashboard",
        )


class TestCreateTokensForUser:
    def test_returns_access_and_refresh_tokens(self, user):
        from apps.accounts.services import create_tokens_for_user

        tokens = create_tokens_for_user(user)

        assert "access" in tokens
        assert "refresh" in tokens
        assert isinstance(tokens["access"], str)
        assert isinstance(tokens["refresh"], str)

    def test_token_contains_role_and_email_claims(self, user):
        from apps.accounts.services import create_tokens_for_user
        from rest_framework_simplejwt.tokens import AccessToken

        tokens = create_tokens_for_user(user)
        decoded = AccessToken(tokens["access"])

        assert decoded["role"] == "entrepreneur"
        assert decoded["email"] == "test@example.com"


class TestEntrepreneurProfileService:
    def test_get_or_create_profile_creates_new(self, db):
        user = User.objects.create_user(
            email="newfounder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = EntrepreneurProfileService.get_or_create_profile(user)
        assert profile is not None
        assert profile.user == user

    def test_get_or_create_profile_returns_existing(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile1 = EntrepreneurProfileService.get_or_create_profile(user)
        profile2 = EntrepreneurProfileService.get_or_create_profile(user)
        assert profile1.id == profile2.id

    def test_update_profile_updates_fields(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = EntrepreneurProfileService.update_profile(
            user, {"company_name": "Acme Inc", "tagline": "We build things"}
        )
        assert profile.company_name == "Acme Inc"
        assert profile.tagline == "We build things"

    def test_list_public_profiles_respects_is_public(self, db):
        public_user = User.objects.create_user(
            email="public@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        private_user = User.objects.create_user(
            email="private@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        private_user.entrepreneur_profile.is_public = False
        private_user.entrepreneur_profile.save()

        profiles = EntrepreneurProfileService.list_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert public_user.entrepreneur_profile.id in profile_ids
        assert private_user.entrepreneur_profile.id not in profile_ids

    def test_list_public_profiles_filters_by_industry(self, db):
        user_tech = User.objects.create_user(
            email="tech@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        user_tech.entrepreneur_profile.industry = "Tech"
        user_tech.entrepreneur_profile.save()

        user_finance = User.objects.create_user(
            email="finance@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        user_finance.entrepreneur_profile.industry = "Finance"
        user_finance.entrepreneur_profile.save()

        profiles = EntrepreneurProfileService.list_public_profiles(industry="Tech")
        profile_ids = [p.id for p in profiles]
        assert user_tech.entrepreneur_profile.id in profile_ids
        assert user_finance.entrepreneur_profile.id not in profile_ids

    def test_get_profile_completeness_returns_percentage(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        completeness = EntrepreneurProfileService.get_profile_completeness(user)
        assert "total" in completeness
        assert "filled" in completeness
        assert "percentage" in completeness
        assert "missing" in completeness
        assert isinstance(completeness["percentage"], int)
        assert 0 <= completeness["percentage"] <= 100

    def test_get_profile_completeness_empty_profile(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        completeness = EntrepreneurProfileService.get_profile_completeness(user)
        assert completeness["filled"] == 0
        assert completeness["percentage"] == 0

    def test_get_profile_completeness_partial(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = user.entrepreneur_profile
        profile.company_name = "Acme Inc"
        profile.industry = "Tech"
        profile.country = "US"
        profile.save()

        completeness = EntrepreneurProfileService.get_profile_completeness(user)
        assert completeness["filled"] >= 3

    def test_get_public_profile_by_id_returns_profile(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile = EntrepreneurProfileService.get_public_profile_by_id(
            user.entrepreneur_profile.id
        )
        assert profile is not None
        assert profile.id == user.entrepreneur_profile.id

    def test_get_public_profile_by_id_returns_none_for_private(self, db):
        user = User.objects.create_user(
            email="founder@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        profile_obj = user.entrepreneur_profile
        profile_obj.is_public = False
        profile_obj.save()

        profile = EntrepreneurProfileService.get_public_profile_by_id(profile_obj.id)
        assert profile is None

    def test_get_public_profile_by_id_nonexistent(self, db):
        profile = EntrepreneurProfileService.get_public_profile_by_id(99999)
        assert profile is None


class TestInvestorProfileService:
    def test_get_or_create_profile_creates_new(self, db):
        user = User.objects.create_user(
            email="newinvestor@example.com",
            password="testpass123",
            role="investor",
        )
        profile = InvestorProfileService.get_or_create_profile(user)
        assert profile is not None
        assert profile.user == user

    def test_get_or_create_profile_returns_existing(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        profile1 = InvestorProfileService.get_or_create_profile(user)
        profile2 = InvestorProfileService.get_or_create_profile(user)
        assert profile1.id == profile2.id

    def test_update_profile_updates_fields(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        profile = InvestorProfileService.update_profile(
            user, {"bio": "Experienced angel investor", "city": "San Francisco"}
        )
        assert profile.bio == "Experienced angel investor"
        assert profile.city == "San Francisco"

    def test_list_public_profiles_respects_is_public(self, db):
        public_user = User.objects.create_user(
            email="public@investor.com",
            password="testpass123",
            role="investor",
        )
        private_user = User.objects.create_user(
            email="private@investor.com",
            password="testpass123",
            role="investor",
        )
        private_user.investor_profile.is_public = False
        private_user.investor_profile.save()

        profiles = InvestorProfileService.list_public_profiles()
        profile_ids = [p.id for p in profiles]
        assert public_user.investor_profile.id in profile_ids
        assert private_user.investor_profile.id not in profile_ids

    def test_list_public_profiles_filters_by_industry(self, db):
        user_tech = User.objects.create_user(
            email="tech@investor.com",
            password="testpass123",
            role="investor",
        )
        user_tech.investor_profile.preferred_industries = ["Tech"]
        user_tech.investor_profile.save()

        user_finance = User.objects.create_user(
            email="finance@investor.com",
            password="testpass123",
            role="investor",
        )
        user_finance.investor_profile.preferred_industries = ["Finance"]
        user_finance.investor_profile.save()

        profiles = InvestorProfileService.list_public_profiles(industry="Tech")
        profile_ids = [p.id for p in profiles]
        assert user_tech.investor_profile.id in profile_ids
        assert user_finance.investor_profile.id not in profile_ids

    def test_get_profile_completeness_returns_percentage(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        completeness = InvestorProfileService.get_profile_completeness(user)
        assert "total" in completeness
        assert "filled" in completeness
        assert "percentage" in completeness
        assert "missing" in completeness
        assert isinstance(completeness["percentage"], int)

    def test_get_profile_completeness_empty_profile(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        completeness = InvestorProfileService.get_profile_completeness(user)
        assert completeness["filled"] == 0
        assert completeness["percentage"] == 0

    def test_get_public_profile_by_id_returns_profile(self, db):
        user = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            role="investor",
        )
        profile = InvestorProfileService.get_public_profile_by_id(
            user.investor_profile.id
        )
        assert profile is not None
        assert profile.id == user.investor_profile.id

    def test_get_public_profile_by_id_nonexistent(self, db):
        profile = InvestorProfileService.get_public_profile_by_id(99999)
        assert profile is None

    def test_get_investor_statistics_returns_aggregates(self, db):
        for i in range(3):
            user = User.objects.create_user(
                email=f"investor{i}@example.com",
                password="testpass123",
                role="investor",
            )
            user.investor_profile.investor_type = "angel"
            user.investor_profile.ticket_size_min = 10000
            user.investor_profile.ticket_size_max = 100000
            user.investor_profile.years_of_experience = 5
            user.investor_profile.lead_investor = True
            user.investor_profile.save()

        stats = InvestorProfileService.get_investor_statistics()

        assert stats["total_investors"] >= 3
        assert "by_type" in stats
        assert stats["by_type"].get("angel", 0) >= 3
        assert stats["lead_investors"] >= 3
        assert stats["avg_ticket_min"] is not None
        assert stats["avg_ticket_max"] is not None
        assert stats["avg_experience"] is not None
