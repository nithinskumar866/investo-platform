from .base import *

DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "investo_test",
        "USER": config("DB_USER", default="investo"),
        "PASSWORD": config("DB_PASSWORD", default="investo"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable throttle in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": None,
    "user": None,
    "otp_request": None,
    "resend_verification": None,
    "auth_ip": None,
    "login_attempt": None,
}

# Disable unwanted middleware
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]

# Use local file storage in tests
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Cache: use local memory (fastest for tests)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# Disable Celery tasks in tests (run synchronously)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Minimal email backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Never call a local model from tests
MATCH_EMBEDDINGS_ENABLED = False
MATCH_AI_PROVIDER = "apps.match_intelligence.providers.RuleBasedProvider"
