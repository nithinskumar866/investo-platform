from django.contrib import admin
from .models import PlatformSetting, FeatureFlag, MaintenanceMode

@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ["key", "group", "value_type", "is_public", "is_encrypted", "updated_at"]
    list_filter = ["group", "value_type", "is_public"]
    search_fields = ["key", "label"]

@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ["key", "enabled", "user_percentage", "updated_at"]
    list_filter = ["enabled"]
    search_fields = ["key", "label"]

@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ["is_active", "started_at", "expected_end_at"]
