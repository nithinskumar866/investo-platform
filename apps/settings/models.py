from django.db import models


class PlatformSetting(models.Model):
    class ValueType(models.TextChoices):
        STRING = "string", "String"
        INTEGER = "integer", "Integer"
        FLOAT = "float", "Float"
        BOOLEAN = "boolean", "Boolean"
        JSON = "json", "JSON"

    key = models.SlugField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    value_type = models.CharField(max_length=10, choices=ValueType.choices, default=ValueType.STRING)
    string_value = models.TextField(blank=True, default="")
    integer_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    boolean_value = models.BooleanField(default=False)
    json_value = models.JSONField(default=dict, blank=True)
    group = models.CharField(max_length=100, blank=True, default="general", db_index=True)
    is_public = models.BooleanField(default=False, help_text="Exposed via public API")
    is_encrypted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings_platform_setting"
        ordering = ["group", "key"]

    def __str__(self):
        return f"{self.group}/{self.key}"

    def get_value(self):
        return {
            "string": self.string_value,
            "integer": self.integer_value,
            "float": self.float_value,
            "boolean": self.boolean_value,
            "json": self.json_value,
        }.get(self.value_type)

    def set_value(self, value):
        field_map = {
            "string": "string_value",
            "integer": "integer_value",
            "float": "float_value",
            "boolean": "boolean_value",
            "json": "json_value",
        }
        setattr(self, field_map[self.value_type], value)


class FeatureFlag(models.Model):
    key = models.SlugField(max_length=100, unique=True, db_index=True)
    label = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=False)
    enabled_for_roles = models.JSONField(default=list, blank=True, help_text="List of roles that can access this feature")
    user_percentage = models.PositiveIntegerField(default=100, help_text="Percentage of users (0-100) who see this feature")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings_feature_flag"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key}={'ON' if self.enabled else 'OFF'}"


class MaintenanceMode(models.Model):
    is_active = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True, default="Under Maintenance")
    message = models.TextField(blank=True, default="We are performing scheduled maintenance. Please check back shortly.")
    allowed_ips = models.JSONField(default=list, blank=True, help_text="IPs that can bypass maintenance mode")
    allowed_user_ids = models.JSONField(default=list, blank=True, help_text="User IDs that can bypass")
    started_at = models.DateTimeField(null=True, blank=True)
    expected_end_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings_maintenance_mode"
        verbose_name = "Maintenance Mode"

    def __str__(self):
        return f"Maintenance: {'Active' if self.is_active else 'Inactive'}"
