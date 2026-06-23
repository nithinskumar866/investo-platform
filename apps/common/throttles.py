from rest_framework.throttling import SimpleRateThrottle


class OTPRequestThrottle(SimpleRateThrottle):
    """Rate limiter for OTP-based endpoints (verify email, reset password, etc.)."""

    scope = "otp_request"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "") or request.query_params.get("email", "")
        if email:
            return self.cache_format % {"scope": self.scope, "ident": email.lower().strip()}
        if request.user.is_authenticated:
            return self.cache_format % {"scope": self.scope, "ident": request.user.pk}
        ident = request.META.get("REMOTE_ADDR", "")
        return self.cache_format % {"scope": self.scope, "ident": ident}


class LoginRateThrottle(SimpleRateThrottle):
    scope = "login_attempt"

    def get_cache_key(self, request, view):
        try:
            email = request.data.get("email", "") if request.data else ""
        except Exception:
            email = ""
        if email:
            return self.cache_format % {"scope": self.scope, "ident": email.lower().strip()}
        ident = request.META.get("REMOTE_ADDR", "")
        return self.cache_format % {"scope": self.scope, "ident": ident}


class ResendVerificationThrottle(SimpleRateThrottle):
    """
    Stricter throttle for resend endpoints to prevent email spam.
    Limits to 3 requests per hour per email.
    """

    scope = "resend_verification"

    def get_cache_key(self, request, view):
        email = request.data.get("email", "") or request.query_params.get("email", "")
        if email:
            return self.cache_format % {"scope": self.scope, "ident": email.lower().strip()}
        return None
