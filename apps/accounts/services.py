import random
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.core.mail import send_mail

User = get_user_model()
logger = logging.getLogger(__name__)


def create_tokens_for_user(user):
    """
    Create JWT token pair with custom claims for the given user.

    Why a standalone function instead of subclassing tokens:
    simplejwt's RefreshToken.for_user() creates tokens from the
    base class, which doesn't include our custom claims (role, email).
    We add them here after creation — simpler than subclassing four
    token classes.

    Why role in the token:
    Every protected API response needs to check the user's role for
    permission decisions. Including it in the JWT avoids a DB lookup
    or /me/ call on every request. The tradeoff is that if a user's
    role changes, they need a new token — but role changes are rare
    and usually require admin action, so a 15-min access token window
    is acceptable.

    Claims added to ALL tokens (access + refresh):
    - role: Used for permission checks without DB lookup
    - email: Used for identifying the user in logs and notifications

    Returns dict with 'access' and 'refresh' token strings.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["email"] = user.email

    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


class AuthService:
    """
    Business logic for authentication operations.

    Why a service layer:
    Views should only handle HTTP concerns (request parsing, response
    formatting). Business logic like "send a verification email with
    a 6-digit OTP" belongs here. This makes the logic testable without
    HTTP, and reusable across views, management commands, and Celery tasks.

    Architecture pattern: Service objects are stateless. All state is
    passed as parameters. This makes them thread-safe and easy to test.
    """

    @staticmethod
    def _generate_otp() -> str:
        """Generate a 6-digit OTP."""
        return f"{random.randint(100000, 999999)}"

    @staticmethod
    def _hash_otp(otp: str) -> str:
        """Hash OTP before storing. Never store plaintext OTPs."""
        return hashlib.sha256(otp.encode()).hexdigest()

    @staticmethod
    def send_verification_email(user) -> str:
        """
        Generate and send email verification OTP.
        Returns the plaintext OTP (for testing/development).
        In production, only the hash is stored — the OTP is sent via email.
        """
        otp = AuthService._generate_otp()
        otp_hash = AuthService._hash_otp(otp)
        cache_key = f"otp:verify:{user.email}"

        cache.set(cache_key, otp_hash, timeout=600)

        try:
            send_mail(
                subject="Verify your Investo account",
                message=f"Your verification code is: {otp}\n\nThis code expires in 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Verification email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            raise

        return otp

    @staticmethod
    def verify_email(email: str, otp: str) -> bool:
        """
        Verify a user's email using OTP.

        Why Redis-based OTP (not DB):
        - OTPs are ephemeral (10-min TTL) — Redis auto-expires them
        - No need for a separate table or cleanup job
        - Redis SET with TTL is a single atomic operation
        - Fast: sub-millisecond lookup vs DB query
        """
        cache_key = f"otp:verify:{email.lower().strip()}"
        stored_hash = cache.get(cache_key)

        if not stored_hash:
            logger.warning(f"Verification attempt with expired or missing OTP for {email}")
            return False

        if stored_hash != AuthService._hash_otp(otp):
            logger.warning(f"Invalid OTP attempt for {email}")
            return False

        user = User.objects.filter(email=email.lower().strip()).first()
        if user:
            user.is_verified = True
            user.email_verified_at = __import__("django").utils.timezone.now()
            user.save(update_fields=["is_verified", "email_verified_at"])
            cache.delete(cache_key)
            logger.info(f"Email verified for {email}")
            return True

        return False

    @staticmethod
    def send_password_reset_otp(email: str) -> str:
        """Generate and send password reset OTP."""
        user = User.objects.filter(email=email.lower().strip()).first()
        if not user:
            logger.info(f"Password reset requested for non-existent email: {email}")
            return ""

        otp = AuthService._generate_otp()
        otp_hash = AuthService._hash_otp(otp)
        cache_key = f"otp:reset:{user.email}"
        cache.set(cache_key, otp_hash, timeout=600)

        try:
            send_mail(
                subject="Reset your Investo password",
                message=f"Your password reset code is: {otp}\n\nThis code expires in 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.info(f"Password reset OTP sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
            raise

        return otp

    @staticmethod
    def reset_password(email: str, otp: str, new_password: str) -> bool:
        """Verify OTP and reset password."""
        cache_key = f"otp:reset:{email.lower().strip()}"
        stored_hash = cache.get(cache_key)

        if not stored_hash or stored_hash != AuthService._hash_otp(otp):
            logger.warning(f"Invalid or expired password reset OTP for {email}")
            return False

        user = User.objects.filter(email=email.lower().strip()).first()
        if not user:
            return False

        user.set_password(new_password)
        user.save(update_fields=["password"])
        cache.delete(cache_key)
        logger.info(f"Password reset successful for {email}")
        return True
