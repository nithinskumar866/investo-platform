from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Use console email in development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += [
    "debug_toolbar",
]

MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Relax throttle rates in development
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000/hour",
    "user": "10000/minute",
    "login_attempt": "1000/hour",
    "otp_request": "1000/hour",
    "resend_verification": "100/hour",
}

# Allow browsable API in development only
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Override database for local development convenience
import os
if not os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "investo",
            "USER": "investo",
            "PASSWORD": "investo",
            "HOST": "localhost",
            "PORT": "5432",
            "CONN_MAX_AGE": 0,
        }
    }

# Cache: shorter TTLs in development
CACHES["default"]["TIMEOUT"] = 60
CACHES["default"]["KEY_PREFIX"] = "investo_dev"
