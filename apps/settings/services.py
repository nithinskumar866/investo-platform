import logging

from .models import PlatformSetting, FeatureFlag, MaintenanceMode
from .repositories import SettingsRepository

logger = logging.getLogger(__name__)


class SettingsService:
    @staticmethod
    def get_setting(key: str):
        return SettingsRepository.get_setting(key)

    @staticmethod
    def get_settings_by_group(group: str):
        return SettingsRepository.get_settings_by_group(group)

    @staticmethod
    def get_public_settings():
        return SettingsRepository.get_public_settings()

    @staticmethod
    def set_setting(key: str, value, updated_by):
        setting = SettingsRepository.get_setting_or_none(key)
        if not setting:
            logger.warning(f"Setting {key} not found")
            return None
        setting.set_value(value)
        setting.save(update_fields=[f"{setting.value_type}_value", "updated_at"])
        return setting

    @staticmethod
    def update_or_create_setting(key: str, label: str, value, value_type: str = "string", group: str = "general"):
        field_map = {
            "string": "string_value",
            "integer": "integer_value",
            "float": "float_value",
            "boolean": "boolean_value",
            "json": "json_value",
        }
        value_field = field_map.get(value_type, "string_value")
        setting, created = PlatformSetting.objects.update_or_create(
            key=key,
            defaults={
                "label": label,
                "value_type": value_type,
                "group": group,
                value_field: value,
            },
        )
        return setting

    @staticmethod
    def delete_setting(key: str):
        deleted, _ = PlatformSetting.objects.filter(key=key).delete()
        return deleted > 0

    # Feature flags
    @staticmethod
    def is_feature_enabled(key: str, user=None) -> bool:
        flag = SettingsRepository.get_feature_flag(key)
        if not flag or not flag.enabled:
            return False
        if flag.user_percentage < 100 and user:
            if (user.id % 100) >= flag.user_percentage:
                return False
        if flag.enabled_for_roles and user and user.role not in flag.enabled_for_roles:
            return False
        return True

    @staticmethod
    def get_all_flags():
        return SettingsRepository.get_all_flags()

    @staticmethod
    def toggle_flag(key: str, enabled: bool):
        flag = FeatureFlag.objects.filter(key=key).first()
        if not flag:
            return None
        flag.enabled = enabled
        flag.save(update_fields=["enabled", "updated_at"])
        return flag

    @staticmethod
    def update_or_create_flag(key: str, label: str, enabled: bool = False, **kwargs):
        flag, _ = FeatureFlag.objects.update_or_create(
            key=key,
            defaults={"label": label, "enabled": enabled, **kwargs},
        )
        return flag

    # Maintenance mode
    @staticmethod
    def get_maintenance_mode():
        mode = MaintenanceMode.objects.first()
        if not mode:
            mode = MaintenanceMode.objects.create()
        return mode

    @staticmethod
    def set_maintenance(active: bool, request):
        mode = SettingsService.get_maintenance_mode()
        mode.is_active = active
        if active:
            from django.utils import timezone
            mode.started_at = timezone.now()
        else:
            mode.started_at = None
            mode.expected_end_at = None
        mode.save(update_fields=["is_active", "started_at", "expected_end_at", "updated_at"])
        return mode

    @staticmethod
    def check_maintenance_access(request) -> bool:
        mode = SettingsService.get_maintenance_mode()
        if not mode.is_active:
            return True
        ip = request.META.get("REMOTE_ADDR", "")
        if ip in mode.allowed_ips:
            return True
        if request.user.is_authenticated and request.user.id in mode.allowed_user_ids:
            return True
        if request.user.is_authenticated and request.user.role == "admin":
            return True
        return False
