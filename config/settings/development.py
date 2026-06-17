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
}

# Allow browsable API in development only
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Override database for local development convenience
# If .env provides DATABASE_URL, it takes precedence
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
        }
    }

# Cache: shorter TTLs in development
CACHES["default"]["TIMEOUT"] = 60
CACHES["default"]["KEY_PREFIX"] = "investo_dev"
