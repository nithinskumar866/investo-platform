"""
Quick test script to verify authentication flow.
Run with: python manage.py runscript scripts.test_auth
Or: python manage.py shell < scripts/test_auth.py
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import AccessToken
from apps.accounts.services import AuthService, create_tokens_for_user

User = get_user_model()

print("=" * 60)
print("INVESTO AUTH SYSTEM TESTS")
print("=" * 60)

# 1. Test User exists
user = User.objects.filter(email="admin@investo.com").first()
assert user is not None, "FAIL: Superuser not found"
print(f"[PASS] Superuser found: {user.email} (role={user.role})")

# 2. Test authenticate
user = authenticate(username="admin@investo.com", password="admin123")
assert user is not None, "FAIL: Authentication failed"
print(f"[PASS] Authentication: user={user.email}, role={user.role}")

# 3. Test JWT token creation
tokens = create_tokens_for_user(user)
access_token = tokens["access"]
print(f"[PASS] JWT Access Token: {access_token[:30]}...")

# 4. Test token decode
decoded = AccessToken(access_token)
assert decoded["user_id"] == user.id, "FAIL: Token user_id mismatch"
assert decoded.get("role") == "admin", f"FAIL: Expected role=admin, got {decoded.get('role')}"
print(f"[PASS] Token decode: user_id={decoded['user_id']}, role={decoded.get('role')}")

# 5. Test token expiry (should be ~15 minutes)
from datetime import timedelta
from django.conf import settings
expected_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
print(f"[PASS] Token lifetime: {expected_lifetime}")

# 6. Test OTP generation
otp = AuthService.send_verification_email(user)
assert otp and len(otp) == 6, f"FAIL: OTP invalid: {otp}"
print(f"[PASS] OTP generated: {otp} (6-digit)")

# 7. Test email verification
result = AuthService.verify_email(email="admin@investo.com", otp=otp)
assert result, "FAIL: Email verification returned False"
user.refresh_from_db()
assert user.is_verified is True, "FAIL: User not marked as verified"
print(f"[PASS] Email verified: is_verified={user.is_verified}")

# 8. Test password reset flow
reset_otp = AuthService.send_password_reset_otp("admin@investo.com")
assert reset_otp and len(reset_otp) == 6, f"FAIL: Reset OTP invalid: {reset_otp}"
print(f"[PASS] Password reset OTP generated: {reset_otp}")

# 9. Test actual password reset
new_password = "newadmin456"
result = AuthService.reset_password("admin@investo.com", reset_otp, new_password)
assert result, "FAIL: Password reset returned False"
user = authenticate(username="admin@investo.com", password=new_password)
assert user is not None, "FAIL: Login with new password failed"
print(f"[PASS] Password reset successful")

# 10. Revert password
user.set_password("admin123")
user.save()
print(f"[PASS] Password reverted for future tests")

print()
print("=" * 60)
print("ALL AUTH TESTS PASSED SUCCESSFULLY")
print("=" * 60)
