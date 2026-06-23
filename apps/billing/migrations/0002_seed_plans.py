from django.db import migrations


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("billing", "SubscriptionPlan")

    plans = [
        {
            "name": "Free",
            "slug": "free",
            "tier": "free",
            "description": "Get started with basic access to the Investo platform.",
            "monthly_price": 0,
            "yearly_price": 0,
            "sort_order": 0,
            "features": {
                "basic_matching": True,
                "basic_search": True,
                "profile_visibility": True,
                "ai_pitch_improvement": False,
                "advanced_search": False,
                "deal_analytics": False,
                "data_room_storage": False,
                "founder_contact_unlock": False,
                "export_capabilities": False,
                "priority_visibility": False,
                "advanced_reporting": False,
                "priority_recommendations": False,
                "unlimited_matches": False,
            },
            "limits": {
                "matches": 10,
                "daily_views": 20,
                "conversations": 5,
                "data_room_documents": 0,
                "saved_searches": 3,
            },
        },
        {
            "name": "Founder Premium",
            "slug": "founder-premium",
            "tier": "founder_premium",
            "description": "Unlock powerful tools for founders to attract investors and grow.",
            "monthly_price": 29.00,
            "yearly_price": 290.00,
            "sort_order": 1,
            "is_popular": True,
            "features": {
                "basic_matching": True,
                "basic_search": True,
                "profile_visibility": True,
                "ai_pitch_improvement": True,
                "advanced_search": True,
                "unlimited_startup_views": True,
                "deal_analytics": False,
                "data_room_storage": True,
                "founder_contact_unlock": False,
                "export_capabilities": False,
                "priority_visibility": True,
                "advanced_reporting": True,
                "priority_recommendations": False,
                "unlimited_matches": False,
            },
            "limits": {
                "daily_views": 999999,
                "conversations": 50,
                "data_room_documents": 100,
                "saved_searches": 20,
            },
        },
        {
            "name": "Investor Premium",
            "slug": "investor-premium",
            "tier": "investor_premium",
            "description": "Empower your deal flow with advanced analytics and founder access.",
            "monthly_price": 49.00,
            "yearly_price": 490.00,
            "sort_order": 2,
            "is_popular": True,
            "features": {
                "basic_matching": True,
                "basic_search": True,
                "profile_visibility": True,
                "ai_pitch_improvement": False,
                "advanced_search": True,
                "unlimited_startup_views": True,
                "deal_analytics": True,
                "data_room_storage": False,
                "founder_contact_unlock": True,
                "export_capabilities": True,
                "priority_visibility": False,
                "advanced_reporting": False,
                "priority_recommendations": True,
                "unlimited_matches": True,
            },
            "limits": {
                "daily_views": 999999,
                "conversations": 200,
                "saved_searches": 50,
            },
        },
        {
            "name": "Enterprise",
            "slug": "enterprise",
            "tier": "enterprise",
            "description": "Custom solutions for organizations with advanced needs.",
            "monthly_price": 199.00,
            "yearly_price": 1990.00,
            "sort_order": 3,
            "features": {
                "basic_matching": True,
                "basic_search": True,
                "profile_visibility": True,
                "ai_pitch_improvement": True,
                "advanced_search": True,
                "unlimited_startup_views": True,
                "deal_analytics": True,
                "data_room_storage": True,
                "founder_contact_unlock": True,
                "export_capabilities": True,
                "priority_visibility": True,
                "advanced_reporting": True,
                "priority_recommendations": True,
                "unlimited_matches": True,
            },
            "limits": {},
        },
    ]

    for plan_data in plans:
        SubscriptionPlan.objects.update_or_create(
            slug=plan_data["slug"],
            defaults=plan_data,
        )


def reverse_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("billing", "SubscriptionPlan")
    SubscriptionPlan.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_plans, reverse_plans),
    ]
