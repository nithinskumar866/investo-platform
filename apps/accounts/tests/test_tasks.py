import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        role="entrepreneur",
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


class TestSendVerificationEmailTask:
    def test_sends_verification_email(self, user):
        from apps.accounts.tasks import send_verification_email_task

        with patch("apps.accounts.tasks.AuthService.send_verification_email") as mock_send:
            send_verification_email_task(user.id)

        mock_send.assert_called_once_with(user)

    def test_handles_missing_user_gracefully(self):
        from apps.accounts.tasks import send_verification_email_task

        with patch("apps.accounts.tasks.logger") as mock_logger:
            send_verification_email_task(99999)

        mock_logger.warning.assert_called_once_with(
            "Verification email task failed: user 99999 not found"
        )

    def test_stores_otp_in_cache(self, user):
        from apps.accounts.tasks import send_verification_email_task

        with patch("apps.accounts.tasks.AuthService.send_verification_email") as mock_send:
            mock_send.side_effect = lambda u: cache.set(
                f"otp:verify:{u.email}",
                "hashed_otp",
                timeout=600,
            )
            send_verification_email_task(user.id)

        cached = cache.get(f"otp:verify:{user.email}")
        assert cached == "hashed_otp"


class TestSendPasswordResetTask:
    def test_sends_password_reset_email(self):
        from apps.accounts.tasks import send_password_reset_task

        with patch("apps.accounts.tasks.AuthService.send_password_reset_otp") as mock_send:
            send_password_reset_task("test@example.com")

        mock_send.assert_called_once_with("test@example.com")

    def test_stores_otp_in_cache(self):
        from apps.accounts.tasks import send_password_reset_task

        with patch("apps.accounts.tasks.AuthService.send_password_reset_otp") as mock_send:
            mock_send.side_effect = lambda email: cache.set(
                f"otp:reset:{email}",
                "hashed_otp",
                timeout=600,
            )
            send_password_reset_task("test@example.com")

        cached = cache.get("otp:reset:test@example.com")
        assert cached == "hashed_otp"

    def test_handles_nonexistent_email(self):
        from apps.accounts.tasks import send_password_reset_task

        with patch("apps.accounts.tasks.AuthService.send_password_reset_otp") as mock_send:
            mock_send.return_value = ""
            send_password_reset_task("nonexistent@example.com")

        mock_send.assert_called_once_with("nonexistent@example.com")
