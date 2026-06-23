from rest_framework import serializers
from .models import PlatformSetting, FeatureFlag, MaintenanceMode


class PlatformSettingSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = PlatformSetting
        fields = ["id", "key", "label", "description", "value_type", "value", "group", "is_public", "updated_at"]
        read_only_fields = ["id", "key", "value_type", "updated_at"]

    def get_value(self, obj):
        return obj.get_value()


class PlatformSettingUpdateSerializer(serializers.Serializer):
    value = serializers.JSONField()


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class FeatureFlagToggleSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()


class MaintenanceModeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceMode
        fields = ["is_active", "title", "message", "allowed_ips", "allowed_user_ids", "started_at", "expected_end_at"]
        read_only_fields = ["started_at"]


class MaintenanceModeUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
    title = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    expected_end_at = serializers.DateTimeField(required=False, allow_null=True)
    allowed_ips = serializers.JSONField(required=False)
    allowed_user_ids = serializers.JSONField(required=False)


class FeatureAccessSerializer(serializers.Serializer):
    key = serializers.CharField()
    enabled = serializers.BooleanField()
