from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="FeatureFlag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(max_length=100, unique=True, db_index=True)),
                ("label", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("enabled", models.BooleanField(default=False)),
                ("enabled_for_roles", models.JSONField(default=list, blank=True)),
                ("user_percentage", models.PositiveIntegerField(default=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["key"], "db_table": "settings_feature_flag"},
        ),
        migrations.CreateModel(
            name="MaintenanceMode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=False)),
                ("title", models.CharField(blank=True, default="Under Maintenance", max_length=255)),
                ("message", models.TextField(blank=True, default="We are performing scheduled maintenance. Please check back shortly.")),
                ("allowed_ips", models.JSONField(default=list, blank=True)),
                ("allowed_user_ids", models.JSONField(default=list, blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("expected_end_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "settings_maintenance_mode", "verbose_name": "Maintenance Mode"},
        ),
        migrations.CreateModel(
            name="PlatformSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.SlugField(max_length=100, unique=True, db_index=True)),
                ("label", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("value_type", models.CharField(choices=[("string", "String"), ("integer", "Integer"), ("float", "Float"), ("boolean", "Boolean"), ("json", "JSON")], default="string", max_length=10)),
                ("string_value", models.TextField(blank=True, default="")),
                ("integer_value", models.IntegerField(blank=True, null=True)),
                ("float_value", models.FloatField(blank=True, null=True)),
                ("boolean_value", models.BooleanField(default=False)),
                ("json_value", models.JSONField(default=dict, blank=True)),
                ("group", models.CharField(blank=True, db_index=True, default="general", max_length=100)),
                ("is_public", models.BooleanField(default=False)),
                ("is_encrypted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "settings_platform_setting", "ordering": ["group", "key"]},
        ),
    ]
