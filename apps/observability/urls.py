from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.ops_health, name="ops-health"),
    path("metrics/", views.ops_metrics, name="ops-metrics"),
    path("errors/", views.ops_errors, name="ops-errors"),
    path("jobs/", views.ops_jobs, name="ops-jobs"),
    path("alerts/", views.ops_alerts, name="ops-alerts"),
]
