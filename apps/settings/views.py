from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import IsAdmin
from apps.common.exceptions import ApplicationError

from .serializers import (
    PlatformSettingSerializer,
    PlatformSettingUpdateSerializer,
    FeatureFlagSerializer,
    FeatureFlagToggleSerializer,
    MaintenanceModeSerializer,
    MaintenanceModeUpdateSerializer,
    FeatureAccessSerializer,
)
from .services import SettingsService


@api_view(["GET"])
@permission_classes([AllowAny])
def public_settings(request):
    settings = SettingsService.get_public_settings()
    serializer = PlatformSettingSerializer(settings, many=True)
    return Response({s.key: s.get_value() for s in settings})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdmin])
def platform_setting_detail(request, key):
    setting = SettingsService.get_setting(key)
    if not setting:
        raise ApplicationError("Setting not found", "NOT_FOUND", 404)

    if request.method == "GET":
        serializer = PlatformSettingSerializer(setting)
        return Response(serializer.data)

    serializer = PlatformSettingUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    updated = SettingsService.set_setting(key, serializer.validated_data["value"], request.user)
    result = PlatformSettingSerializer(updated)
    return Response(result.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def feature_access(request):
    key = request.query_params.get("key")
    if not key:
        raise ApplicationError("key query parameter required", "MISSING_PARAM", 400)
    enabled = SettingsService.is_feature_enabled(key, request.user if request.user.is_authenticated else None)
    return Response({"key": key, "enabled": enabled})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def feature_flag_list(request):
    if request.method == "GET":
        flags = SettingsService.get_all_flags()
        serializer = FeatureFlagSerializer(flags, many=True)
        return Response(serializer.data)
    serializer = FeatureFlagSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    flag = SettingsService.update_or_create_flag(**serializer.validated_data)
    result = FeatureFlagSerializer(flag)
    return Response(result.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def feature_flag_toggle(request, key):
    serializer = FeatureFlagToggleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    flag = SettingsService.toggle_flag(key, serializer.validated_data["enabled"])
    if not flag:
        raise ApplicationError("Feature flag not found", "NOT_FOUND", 404)
    result = FeatureFlagSerializer(flag)
    return Response(result.data)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdmin])
def maintenance_mode(request):
    if request.method == "GET":
        mode = SettingsService.get_maintenance_mode()
        serializer = MaintenanceModeSerializer(mode)
        return Response(serializer.data)

    serializer = MaintenanceModeUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    mode = SettingsService.set_maintenance(serializer.validated_data["is_active"], request)
    if serializer.validated_data.get("expected_end_at"):
        mode.expected_end_at = serializer.validated_data["expected_end_at"]
        mode.save(update_fields=["expected_end_at"])
    result = MaintenanceModeSerializer(mode)
    return Response(result.data)
