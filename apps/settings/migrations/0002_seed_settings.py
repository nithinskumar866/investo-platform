from django.db import migrations


def seed_settings(apps, schema_editor):
    PlatformSetting = apps.get_model("settings", "PlatformSetting")
    FeatureFlag = apps.get_model("settings", "FeatureFlag")

    settings = [
        # Email
        {"key": "email_from_name", "label": "Email From Name", "value_type": "string", "string_value": "Investo", "group": "email", "is_public": False},
        {"key": "email_from_address", "label": "Email From Address", "value_type": "string", "string_value": "noreply@investo.com", "group": "email", "is_public": False},
        {"key": "email_logo_url", "label": "Email Logo URL", "value_type": "string", "string_value": "", "group": "email", "is_public": True},
        # Billing
        {"key": "billing_currency", "label": "Default Currency", "value_type": "string", "string_value": "USD", "group": "billing"},
        {"key": "trial_days", "label": "Trial Duration Days", "value_type": "integer", "integer_value": 14, "group": "billing"},
        {"key": "max_free_matches", "label": "Max Free Tier Matches", "value_type": "integer", "integer_value": 10, "group": "billing", "is_public": True},
        {"key": "max_free_messages", "label": "Max Free Tier Messages", "value_type": "integer", "integer_value": 5, "group": "billing", "is_public": True},
        # Matching
        {"key": "match_recalculation_interval", "label": "Match Recalculation Interval (hours)", "value_type": "integer", "integer_value": 6, "group": "matching"},
        {"key": "match_score_threshold", "label": "Minimum Match Score to Show", "value_type": "float", "float_value": 60.0, "group": "matching", "is_public": True},
        {"key": "max_matches_per_user", "label": "Max Matches Per User", "value_type": "integer", "integer_value": 100, "group": "matching"},
        # Data Room
        {"key": "max_document_size_mb", "label": "Max Document Size (MB)", "value_type": "integer", "integer_value": 50, "group": "data_room"},
        {"key": "allowed_document_types", "label": "Allowed Document MIME Types", "value_type": "json", "json_value": ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "text/plain"], "group": "data_room"},
        # Platform
        {"key": "platform_name", "label": "Platform Name", "value_type": "string", "string_value": "Investo", "group": "platform", "is_public": True},
        {"key": "support_email", "label": "Support Email", "value_type": "string", "string_value": "support@investo.com", "group": "platform", "is_public": True},
        {"key": "maintenance_message", "label": "Maintenance Message", "value_type": "string", "string_value": "We are performing scheduled maintenance. Please check back shortly.", "group": "platform", "is_public": True},
    ]

    for s in settings:
        PlatformSetting.objects.update_or_create(key=s.pop("key"), defaults=s)

    flags = [
        {"key": "ai_match_insights", "label": "AI Match Insights", "enabled": True},
        {"key": "video_meetings", "label": "Video Meeting Support", "enabled": True, "user_percentage": 50},
        {"key": "data_room_analytics", "label": "Data Room Analytics", "enabled": True},
        {"key": "investment_term_sheets", "label": "Digital Term Sheets", "enabled": True},
        {"key": "bulk_notifications", "label": "Bulk Push Notifications", "enabled": False},
        {"key": "startup_verification_badge", "label": "Startup Verification Badge", "enabled": True},
    ]

    for f in flags:
        FeatureFlag.objects.update_or_create(key=f.pop("key"), defaults=f)


def reverse_settings(apps, schema_editor):
    PlatformSetting = apps.get_model("settings", "PlatformSetting")
    FeatureFlag = apps.get_model("settings", "FeatureFlag")
    PlatformSetting.objects.all().delete()
    FeatureFlag.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("settings", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(seed_settings, reverse_settings),
    ]
