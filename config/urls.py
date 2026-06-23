from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.observability.views import health, health_db, health_redis, health_storage, health_celery

urlpatterns = [
    path("admin/", admin.site.urls),
    # Public health checks (root level)
    path("health/", health, name="health-root"),
    path("health/db/", health_db, name="health-db-root"),
    path("health/redis/", health_redis, name="health-redis-root"),
    path("health/storage/", health_storage, name="health-storage-root"),
    path("health/celery/", health_celery, name="health-celery-root"),
    # API routes
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/startups/", include("apps.startups.urls")),
    path("api/v1/matching/", include("apps.matching.urls")),
    path("api/v1/matching/", include("apps.match_intelligence.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),
    path("api/v1/investments/", include("apps.investments.urls")),
    path("api/v1/data-room/", include("apps.data_room.urls")),
    path("api/v1/meetings/", include("apps.meetings.urls")),
    path("api/v1/activity/", include("apps.activity_feed.urls")),
    path("api/v1/search/", include("apps.search_app.urls")),
    path("api/v1/analytics/", include("apps.analytics.urls")),
    path("api/v1/billing/", include("apps.billing.urls")),
    path("api/v1/admin/", include("apps.operations.urls")),
    path("api/v1/ops/", include("apps.observability.urls")),
    path("api/v1/onboarding/", include("apps.onboarding.urls")),
    path("api/v1/settings/", include("apps.settings.urls")),
    path("api/v1/", include("apps.common.urls")),
]

if settings.DEBUG:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
