from .base import *

DEBUG = False

# Security
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"

# Per-IP rate limiting for auth endpoints
SIMPLE_JWT["AUTH_TOKEN_CLASSES"] = ("rest_framework_simplejwt.tokens.AccessToken",)

# Production middleware additions
MIDDLEWARE += [
    "django.middleware.security.SecurityMiddleware",
]

# WhiteNoise for static files
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Email: use SMTP in production
if config("EMAIL_HOST", default=""):
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Logging: JSON format for production log aggregation
LOGGING["handlers"]["console"]["formatter"] = "json"

# Set higher connection pool for production
CACHES["default"]["OPTIONS"]["CONNECTION_POOL_CLASS_KWARGS"]["max_connections"] = 100

# Database connection pooling
DATABASES["default"]["CONN_MAX_AGE"] = config("DB_CONN_MAX_AGE", default=60, cast=int)
