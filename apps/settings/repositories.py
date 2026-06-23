from .models import PlatformSetting, FeatureFlag


class SettingsRepository:
    @staticmethod
    def get_setting(key: str):
        return PlatformSetting.objects.get(key=key)

    @staticmethod
    def get_setting_or_none(key: str):
        return PlatformSetting.objects.filter(key=key).first()

    @staticmethod
    def get_settings_by_group(group: str):
        return PlatformSetting.objects.filter(group=group)

    @staticmethod
    def get_public_settings():
        return PlatformSetting.objects.filter(is_public=True)

    @staticmethod
    def get_all_settings():
        return PlatformSetting.objects.all()

    @staticmethod
    def get_feature_flag(key: str):
        return FeatureFlag.objects.filter(key=key).first()

    @staticmethod
    def get_all_flags():
        return FeatureFlag.objects.all()
