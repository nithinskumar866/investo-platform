import pytest
from unittest.mock import Mock

from apps.accounts.models import User
from apps.settings.models import PlatformSetting, FeatureFlag, MaintenanceMode
from apps.settings.services import SettingsService


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123", role="admin",
        is_staff=True, is_superuser=True,
    )


@pytest.fixture
def string_setting(db):
    return PlatformSetting.objects.create(
        key="site_name",
        label="Site Name",
        value_type=PlatformSetting.ValueType.STRING,
        string_value="Investo",
        group="general",
        is_public=True,
    )


@pytest.fixture
def int_setting(db):
    return PlatformSetting.objects.create(
        key="max_upload_mb",
        label="Max Upload MB",
        value_type=PlatformSetting.ValueType.INTEGER,
        integer_value=50,
        group="limits",
        is_public=False,
    )


@pytest.fixture
def bool_setting(db):
    return PlatformSetting.objects.create(
        key="registration_open",
        label="Registration Open",
        value_type=PlatformSetting.ValueType.BOOLEAN,
        boolean_value=True,
        group="general",
        is_public=True,
    )


@pytest.fixture
def feature_flag(db):
    return FeatureFlag.objects.create(
        key="new_dashboard",
        label="New Dashboard",
        enabled=True,
        user_percentage=100,
        enabled_for_roles=[],
    )


@pytest.fixture
def maintenance(db):
    return MaintenanceMode.objects.create(
        is_active=False,
        title="Under Maintenance",
        message="Scheduled maintenance.",
        allowed_ips=["192.168.1.1"],
        allowed_user_ids=[],
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestPlatformSettingModel:
    def test_create_setting(self, string_setting):
        assert string_setting.pk is not None
        assert str(string_setting) == "general/site_name"

    def test_get_value_string(self, string_setting):
        assert string_setting.get_value() == "Investo"

    def test_get_value_integer(self, int_setting):
        assert int_setting.get_value() == 50

    def test_get_value_boolean(self, bool_setting):
        assert bool_setting.get_value() is True

    def test_set_value(self, string_setting):
        string_setting.set_value("NewName")
        assert string_setting.string_value == "NewName"

    def test_value_type_choices(self):
        assert PlatformSetting.ValueType.STRING == "string"
        assert PlatformSetting.ValueType.JSON == "json"


class TestFeatureFlagModel:
    def test_create_flag(self, feature_flag):
        assert feature_flag.pk is not None
        assert str(feature_flag) == "new_dashboard=ON"

    def test_flag_disabled(self, db):
        flag = FeatureFlag.objects.create(
            key="test_flag", label="Test", enabled=False,
        )
        assert str(flag) == "test_flag=OFF"

    def test_percentage_rollout(self, db):
        flag = FeatureFlag.objects.create(
            key="rollout_test", label="Rollout", enabled=True,
            user_percentage=50,
        )
        assert flag.user_percentage == 50


class TestMaintenanceModeModel:
    def test_create(self, maintenance):
        assert maintenance.pk is not None
        assert str(maintenance) == "Maintenance: Inactive"

    def test_activate(self, maintenance):
        maintenance.is_active = True
        maintenance.save()
        assert str(maintenance) == "Maintenance: Active"


# ── Service tests ────────────────────────────────────────────────────────

class TestSettingsService:
    def test_get_setting(self, string_setting):
        result = SettingsService.get_setting("site_name")
        assert result == string_setting

    def test_get_setting_none(self):
        result = SettingsService.get_setting("nonexistent")
        assert result is None

    def test_get_public_settings(self, string_setting, bool_setting, int_setting):
        settings_list = SettingsService.get_public_settings()
        keys = [s.key for s in settings_list]
        assert "site_name" in keys
        assert "registration_open" in keys
        assert "max_upload_mb" not in keys

    def test_set_setting(self, string_setting):
        updated = SettingsService.set_setting(
            "site_name", "NewInvesto", updated_by="admin",
        )
        assert updated is not None
        assert updated.get_value() == "NewInvesto"

    def test_set_setting_not_found(self):
        result = SettingsService.set_setting("invalid", "val", updated_by="admin")
        assert result is None

    def test_is_feature_enabled_flag_off(self, db):
        FeatureFlag.objects.create(
            key="disabled_flag", label="Disabled", enabled=False,
        )
        assert SettingsService.is_feature_enabled("disabled_flag") is False

    def test_is_feature_enabled_flag_on(self, feature_flag):
        assert SettingsService.is_feature_enabled("new_dashboard") is True

    def test_is_feature_enabled_percentage(self, db):
        flag = FeatureFlag.objects.create(
            key="pct_test", label="PCT", enabled=True, user_percentage=0,
        )
        user = Mock(id=1, role="entrepreneur")
        assert SettingsService.is_feature_enabled("pct_test", user) is False

    def test_is_feature_enabled_role_restricted(self, db):
        flag = FeatureFlag.objects.create(
            key="admin_only", label="Admin Only", enabled=True,
            enabled_for_roles=["admin"],
        )
        user = Mock(id=1, role="entrepreneur")
        assert SettingsService.is_feature_enabled("admin_only", user) is False
        admin = Mock(id=2, role="admin")
        assert SettingsService.is_feature_enabled("admin_only", admin) is True

    def test_toggle_flag(self, feature_flag):
        result = SettingsService.toggle_flag("new_dashboard", False)
        assert result is not None
        assert result.enabled is False

    def test_toggle_flag_not_found(self):
        result = SettingsService.toggle_flag("nonexistent", True)
        assert result is None

    def test_get_maintenance_mode_creates(self, db):
        mode = SettingsService.get_maintenance_mode()
        assert mode is not None

    def test_set_maintenance_on(self, maintenance):
        request = Mock()
        mode = SettingsService.set_maintenance(True, request)
        assert mode.is_active is True

    def test_set_maintenance_off(self, maintenance):
        maintenance.is_active = True
        maintenance.save()
        request = Mock()
        mode = SettingsService.set_maintenance(False, request)
        assert mode.is_active is False

    def test_check_maintenance_access_not_active(self, maintenance):
        request = Mock()
        assert SettingsService.check_maintenance_access(request) is True

    def test_check_maintenance_access_active_blocked(self, maintenance):
        maintenance.is_active = True
        maintenance.save()
        request = Mock()
        request.META = {"REMOTE_ADDR": "10.0.0.1"}
        request.user.is_authenticated = False
        assert SettingsService.check_maintenance_access(request) is False

    def test_check_maintenance_access_allowed_ip(self, maintenance):
        maintenance.is_active = True
        maintenance.save()
        request = Mock()
        request.META = {"REMOTE_ADDR": "192.168.1.1"}
        request.user.is_authenticated = False
        assert SettingsService.check_maintenance_access(request) is True

    def test_check_maintenance_access_admin(self, maintenance):
        maintenance.is_active = True
        maintenance.save()
        request = Mock()
        request.META = {"REMOTE_ADDR": "10.0.0.1"}
        request.user.is_authenticated = True
        request.user.role = "admin"
        assert SettingsService.check_maintenance_access(request) is True


# ── View tests ──────────────────────────────────────────────────────────

class TestSettingsViews:
    def test_public_settings(self, api_client, string_setting, bool_setting):
        resp = api_client.get("/api/v1/settings/settings/public/")
        assert resp.status_code == 200
        data = resp.json()
        assert "site_name" in data

    def test_setting_detail_get(self, admin_client, string_setting):
        resp = admin_client.get("/api/v1/settings/settings/site_name/")
        assert resp.status_code == 200

    def test_setting_detail_update(self, admin_client, string_setting):
        resp = admin_client.patch(
            "/api/v1/settings/settings/site_name/",
            {"value": "UpdatedInvesto"},
            format="json",
        )
        assert resp.status_code == 200

    def test_setting_detail_not_found(self, admin_client):
        resp = admin_client.get("/api/v1/settings/settings/nonexistent/")
        assert resp.status_code == 404

    def test_feature_access(self, api_client, feature_flag):
        resp = api_client.get("/api/v1/settings/features/access/?key=new_dashboard")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_feature_access_missing_key(self, api_client):
        resp = api_client.get("/api/v1/settings/features/access/")
        assert resp.status_code == 400

    def test_feature_flag_list(self, admin_client, feature_flag):
        resp = admin_client.get("/api/v1/settings/features/")
        assert resp.status_code == 200

    def test_feature_flag_create(self, admin_client):
        resp = admin_client.post(
            "/api/v1/settings/features/",
            {"key": "new_feature", "label": "New Feature"},
            format="json",
        )
        assert resp.status_code == 201

    def test_feature_flag_toggle(self, admin_client, feature_flag):
        resp = admin_client.post(
            f"/api/v1/settings/features/{feature_flag.key}/toggle/",
            {"enabled": False},
            format="json",
        )
        assert resp.status_code == 200

    def test_maintenance_get(self, admin_client):
        resp = admin_client.get("/api/v1/settings/maintenance/")
        assert resp.status_code == 200

    def test_maintenance_update(self, admin_client):
        resp = admin_client.patch(
            "/api/v1/settings/maintenance/",
            {"is_active": True, "title": "Maintenance"},
            format="json",
        )
        assert resp.status_code == 200

    def test_setting_permission(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/settings/settings/site_name/")
        assert resp.status_code == 403
