import pytest
from django.urls import reverse
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.services import AuthService
pytestmark = pytest.mark.django_db

# ── Inline Factory Fixtures ──

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com",
        password="testpass123",
        role="entrepreneur",
        first_name="John",
        last_name="Founder",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com",
        password="testpass123",
        role="investor",
        first_name="Alice",
        last_name="Investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        password="testpass123",
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


# ── Registration ──

class TestRegisterView:
    URL = "auth-register"

    def test_valid_registration_returns_201_with_user_and_tokens(self, api_client):
        data = {
            "email": "newuser@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "entrepreneur",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["email"] == "newuser@example.com"
        assert body["data"]["user"]["role"] == "entrepreneur"
        assert "access" in body["data"]["tokens"]
        assert "refresh" in body["data"]["tokens"]
        assert User.objects.filter(email="newuser@example.com").exists()

    def test_duplicate_email_returns_validation_error(self, api_client, user):
        data = {
            "email": user.email,
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "Another",
            "last_name": "User",
            "role": "entrepreneur",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "VALIDATION_ERROR"

    def test_weak_password_returns_validation_error(self, api_client):
        data = {
            "email": "weak@example.com",
            "password": "123",
            "confirm_password": "123",
            "first_name": "Weak",
            "last_name": "Pass",
            "role": "entrepreneur",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"

    def test_password_mismatch_returns_error(self, api_client):
        data = {
            "email": "mismatch@example.com",
            "password": "strongpass123",
            "confirm_password": "differentpass456",
            "first_name": "Mismatch",
            "last_name": "Test",
            "role": "entrepreneur",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"

    def test_registration_creates_entrepreneur_profile(self, api_client):
        data = {
            "email": "founder@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "John",
            "last_name": "Doe",
            "role": "entrepreneur",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 201
        user = User.objects.get(email="founder@example.com")
        assert hasattr(user, "entrepreneur_profile")
        assert user.entrepreneur_profile is not None

    def test_registration_creates_investor_profile(self, api_client):
        data = {
            "email": "angel@example.com",
            "password": "strongpass123",
            "confirm_password": "strongpass123",
            "first_name": "Angel",
            "last_name": "Investor",
            "role": "investor",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 201
        user = User.objects.get(email="angel@example.com")
        assert hasattr(user, "investor_profile")
        assert user.investor_profile is not None


# ── Login ──

class TestLoginView:
    URL = "auth-login"

    def test_valid_credentials_return_200_with_tokens(self, api_client, user):
        data = {"email": "test@example.com", "password": "testpass123"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["email"] == "test@example.com"
        assert "access" in body["data"]["tokens"]
        assert "refresh" in body["data"]["tokens"]

    def test_invalid_credentials_return_401(self, api_client, user):
        data = {"email": "test@example.com", "password": "wrongpassword"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    def test_disabled_account_returns_403(self, api_client, user):
        user.is_active = False
        user.save()
        data = {"email": "test@example.com", "password": "testpass123"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 403
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "ACCOUNT_DISABLED"

    def test_nonexistent_email_returns_401(self, api_client):
        data = {"email": "nonexistent@example.com", "password": "testpass123"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 401
        body = response.json()
        assert body["status"] == "error"

    def test_missing_password_returns_error(self, api_client):
        data = {"email": "test@example.com"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400


# ── Logout ──

class TestLogoutView:
    URL = "auth-logout"

    def test_logout_with_valid_token_returns_200(self, authenticated_client, user):
        refresh = RefreshToken.for_user(user)
        data = {"refresh": str(refresh)}
        response = authenticated_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_logout_without_token_body_returns_200(self, authenticated_client):
        response = authenticated_client.post(reverse(self.URL), {}, format="json")
        assert response.status_code == 200

    def test_logout_unauthenticated_returns_401(self, api_client):
        response = api_client.post(reverse(self.URL), {}, format="json")
        assert response.status_code == 401


# ── Me ──

class TestMeView:
    URL = "auth-me"

    def test_get_me_returns_authenticated_user(self, authenticated_client, user):
        response = authenticated_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["role"] == "entrepreneur"

    def test_get_me_includes_profiles(self, authenticated_client):
        response = authenticated_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert "entrepreneur_profile" in body["data"]
        assert "investor_profile" in body["data"]

    def test_patch_me_updates_user_fields(self, authenticated_client, user):
        data = {"first_name": "Updated", "phone": "+1234567890"}
        response = authenticated_client.patch(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Updated"
        assert user.phone == "+1234567890"

    def test_patch_me_does_not_change_role(self, authenticated_client, user):
        data = {"role": "investor"}
        response = authenticated_client.patch(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.role == "entrepreneur"

    def test_me_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


# ── Verify Email ──

class TestVerifyEmailView:
    URL = "auth-verify-email"

    def test_valid_otp_verifies_email(self, api_client, user):
        otp = AuthService.send_verification_email(user)
        data = {"email": user.email, "otp": otp}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["message"] == "Email verified successfully"
        user.refresh_from_db()
        assert user.is_verified is True

    def test_invalid_otp_returns_error(self, api_client, user):
        AuthService.send_verification_email(user)
        data = {"email": user.email, "otp": "000000"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "INVALID_OTP"

    def test_expired_otp_returns_error(self, api_client, user):
        data = {"email": user.email, "otp": "123456"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "INVALID_OTP"

    def test_missing_fields_returns_error(self, api_client):
        response = api_client.post(reverse(self.URL), {}, format="json")
        assert response.status_code == 400


# ── Resend Verification ──

class TestResendVerificationView:
    URL = "auth-resend-verification"

    def test_resend_to_unverified_user_returns_success(self, api_client, user):
        data = {"email": user.email}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["message"] == "Verification email resent"

    def test_resend_to_verified_user_still_returns_success(self, api_client, user):
        user.is_verified = True
        user.save()
        data = {"email": user.email}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_resend_to_nonexistent_email_returns_success(self, api_client):
        data = {"email": "nonexistent@example.com"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"


# ── Forgot Password ──

class TestForgotPasswordView:
    URL = "auth-forgot-password"

    def test_sends_reset_otp_for_existing_user(self, api_client, user):
        data = {"email": user.email}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_sends_reset_otp_for_nonexistent_user(self, api_client):
        data = {"email": "nonexistent@example.com"}
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_missing_email_returns_error(self, api_client):
        response = api_client.post(reverse(self.URL), {}, format="json")
        assert response.status_code == 400


# ── Reset Password ──

class TestResetPasswordView:
    URL = "auth-reset-password"

    def test_valid_otp_resets_password(self, api_client, user):
        otp = AuthService.send_password_reset_otp(user.email)
        data = {
            "email": user.email,
            "otp": otp,
            "password": "newstrongpass456",
            "confirm_password": "newstrongpass456",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["message"] == "Password reset successfully"
        user.refresh_from_db()
        assert user.check_password("newstrongpass456")

    def test_invalid_otp_returns_error(self, api_client, user):
        AuthService.send_password_reset_otp(user.email)
        data = {
            "email": user.email,
            "otp": "000000",
            "password": "newstrongpass456",
            "confirm_password": "newstrongpass456",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "INVALID_OTP"

    def test_password_mismatch_returns_error(self, api_client, user):
        data = {
            "email": user.email,
            "otp": "123456",
            "password": "newpass123",
            "confirm_password": "mismatch",
        }
        response = api_client.post(reverse(self.URL), data, format="json")
        assert response.status_code == 400


# ── Entrepreneur Profile ──

class TestEntrepreneurProfileView:
    URL = "auth-profile-entrepreneur"

    def test_get_profile_returns_data(self, founder_client, founder):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["email"] == "founder@example.com"

    def test_patch_profile_updates_fields(self, founder_client, founder):
        data = {"company_name": "Acme Corp", "tagline": "Building the future"}
        response = founder_client.patch(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["company_name"] == "Acme Corp"
        assert body["data"]["tagline"] == "Building the future"
        founder.entrepreneur_profile.refresh_from_db()
        assert founder.entrepreneur_profile.company_name == "Acme Corp"

    def test_non_entrepreneur_returns_403(self, investor_client):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 403
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "WRONG_ROLE"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


class TestEntrepreneurProfileCompletenessView:
    URL = "auth-profile-entrepreneur-completeness"

    def test_returns_completeness_percentage(self, founder_client):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "percentage" in body["data"]
        assert "filled" in body["data"]
        assert "total" in body["data"]
        assert "missing" in body["data"]

    def test_non_entrepreneur_returns_403(self, investor_client):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


class TestEntrepreneurProfileStartupsView:
    URL = "auth-profile-entrepreneur-startups"

    def test_returns_empty_list_when_no_startups(self, founder_client):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"] == []

    def test_non_entrepreneur_returns_403(self, investor_client):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


# ── Investor Profile ──

class TestInvestorProfileView:
    URL = "auth-profile-investor"

    def test_get_profile_returns_data(self, investor_client, investor):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["email"] == "investor@example.com"

    def test_patch_profile_updates_fields(self, investor_client, investor):
        data = {"bio": "Experienced VC", "investor_type": "vc"}
        response = investor_client.patch(reverse(self.URL), data, format="json")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["bio"] == "Experienced VC"
        assert body["data"]["investor_type"] == "vc"
        investor.investor_profile.refresh_from_db()
        assert investor.investor_profile.bio == "Experienced VC"

    def test_non_investor_returns_403(self, founder_client):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 403
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "WRONG_ROLE"

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


class TestInvestorProfileCompletenessView:
    URL = "auth-profile-investor-completeness"

    def test_returns_completeness_percentage(self, investor_client):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "percentage" in body["data"]
        assert "filled" in body["data"]
        assert "total" in body["data"]
        assert "missing" in body["data"]

    def test_non_investor_returns_403(self, founder_client):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


class TestInvestorProfileStatisticsView:
    URL = "auth-profile-investor-statistics"

    def test_returns_statistics(self, investor_client):
        response = investor_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert "total_investors" in body["data"]
        assert "by_type" in body["data"]
        assert "avg_ticket_min" in body["data"]

    def test_non_investor_returns_403(self, founder_client):
        response = founder_client.get(reverse(self.URL))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 401


# ── Public Entrepreneur Profiles ──

class TestPublicEntrepreneurProfilesView:
    URL = "public-entrepreneur-profiles"

    def test_list_public_profiles_returns_data(self, api_client, founder):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_list_public_profiles_works_without_auth(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200

    def test_list_public_profiles_filters_by_industry(self, api_client, db):
        user = User.objects.create_user(
            email="tech@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        user.entrepreneur_profile.industry = "Tech"
        user.entrepreneur_profile.save()

        response = api_client.get(reverse(self.URL), {"industry": "Tech"})
        assert response.status_code == 200
        body = response.json()
        ids = [p["id"] for p in body["data"]]
        assert user.entrepreneur_profile.id in ids

    def test_list_public_profiles_does_not_include_private(self, api_client, db):
        user = User.objects.create_user(
            email="private@example.com",
            password="testpass123",
            role="entrepreneur",
        )
        user.entrepreneur_profile.is_public = False
        user.entrepreneur_profile.save()

        response = api_client.get(reverse(self.URL))
        body = response.json()
        ids = [p["id"] for p in body["data"]]
        assert user.entrepreneur_profile.id not in ids


class TestPublicEntrepreneurProfileDetailView:
    URL = "public-entrepreneur-profile-detail"

    def test_returns_profile_detail(self, api_client, founder):
        response = api_client.get(
            reverse(self.URL, kwargs={"profile_id": founder.entrepreneur_profile.id})
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["first_name"] == "John"

    def test_not_found_returns_404(self, api_client):
        response = api_client.get(reverse(self.URL, kwargs={"profile_id": 99999}))
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "NOT_FOUND"

    def test_works_without_auth(self, api_client, founder):
        response = api_client.get(
            reverse(self.URL, kwargs={"profile_id": founder.entrepreneur_profile.id})
        )
        assert response.status_code == 200


# ── Public Investor Profiles ──

class TestPublicInvestorProfilesView:
    URL = "public-investor-profiles"

    def test_list_public_profiles_returns_data(self, api_client, investor):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)

    def test_list_public_profiles_works_without_auth(self, api_client):
        response = api_client.get(reverse(self.URL))
        assert response.status_code == 200

    def test_list_public_profiles_does_not_include_private(self, api_client, db):
        user = User.objects.create_user(
            email="private@investor.com",
            password="testpass123",
            role="investor",
        )
        user.investor_profile.is_public = False
        user.investor_profile.save()

        response = api_client.get(reverse(self.URL))
        body = response.json()
        ids = [p["id"] for p in body["data"]]
        assert user.investor_profile.id not in ids


class TestPublicInvestorProfileDetailView:
    URL = "public-investor-profile-detail"

    def test_returns_profile_detail(self, api_client, investor):
        response = api_client.get(
            reverse(self.URL, kwargs={"profile_id": investor.investor_profile.id})
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["user"]["first_name"] == "Alice"

    def test_not_found_returns_404(self, api_client):
        response = api_client.get(reverse(self.URL, kwargs={"profile_id": 99999}))
        assert response.status_code == 404
        body = response.json()
        assert body["status"] == "error"
        assert body["error"]["code"] == "NOT_FOUND"

    def test_works_without_auth(self, api_client, investor):
        response = api_client.get(
            reverse(self.URL, kwargs={"profile_id": investor.investor_profile.id})
        )
        assert response.status_code == 200


# ── Permission Cross-Cutting Tests ──

class TestPermissionGuards:
    def test_unauthenticated_cannot_access_protected_endpoints(self, api_client):
        protected_urls = [
            "auth-logout",
            "auth-me",
            "auth-profile-entrepreneur",
            "auth-profile-entrepreneur-completeness",
            "auth-profile-entrepreneur-startups",
            "auth-profile-investor",
            "auth-profile-investor-completeness",
            "auth-profile-investor-statistics",
        ]
        for url_name in protected_urls:
            response = api_client.get(reverse(url_name))
            assert response.status_code == 401, f"{url_name} did not return 401"

    def test_public_endpoints_work_without_auth(self, api_client):
        public_urls = [
            "auth-register",
            "auth-login",
            "auth-verify-email",
            "auth-resend-verification",
            "auth-forgot-password",
            "auth-reset-password",
            "public-entrepreneur-profiles",
            "public-investor-profiles",
        ]
        for url_name in public_urls:
            response = api_client.get(reverse(url_name))
            assert response.status_code != 401, f"{url_name} returned 401"
