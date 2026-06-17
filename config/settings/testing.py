from .base import *

DEBUG = False

SECRET_KEY = "test-secret-key-not-for-production"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "investo_test",
        "USER": "investo",
        "PASSWORD": "investo",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable throttle in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}

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
