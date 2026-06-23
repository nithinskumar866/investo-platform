from django.urls import path
from . import views

urlpatterns = [
    path("settings/public/", views.public_settings, name="settings-public"),
    path("settings/<slug:key>/", views.platform_setting_detail, name="settings-detail"),
    path("features/access/", views.feature_access, name="features-access"),
    path("features/", views.feature_flag_list, name="features-list"),
    path("features/<slug:key>/toggle/", views.feature_flag_toggle, name="features-toggle"),
    path("maintenance/", views.maintenance_mode, name="settings-maintenance"),
]
