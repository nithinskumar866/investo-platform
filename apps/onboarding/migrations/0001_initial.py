import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="OnboardingWizard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wizard_type", models.CharField(choices=[("founder", "Founder"), ("investor", "Investor")], max_length=20)),
                ("current_step", models.CharField(blank=True, default="", max_length=100)),
                ("is_complete", models.BooleanField(default=False)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="onboarding_wizard", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Onboarding Wizard",
                "db_table": "onboarding_wizard",
            },
        ),
        migrations.CreateModel(
            name="OnboardingStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("step_key", models.CharField(max_length=100)),
                ("step_label", models.CharField(max_length=255)),
                ("is_completed", models.BooleanField(default=False)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("wizard", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="onboarding.onboardingwizard")),
            ],
            options={
                "verbose_name": "Onboarding Step",
                "ordering": ["id"],
                "db_table": "onboarding_step",
            },
        ),
        migrations.CreateModel(
            name="FounderOnboardingData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("company_name", models.CharField(blank=True, default="", max_length=255)),
                ("tagline", models.CharField(blank=True, default="", max_length=200)),
                ("industry", models.CharField(blank=True, default="", max_length=100)),
                ("funding_stage", models.CharField(blank=True, default="", max_length=50)),
                ("website", models.URLField(blank=True, default="")),
                ("linkedin", models.URLField(blank=True, default="")),
                ("team_size", models.PositiveIntegerField(blank=True, null=True)),
                ("pitch_deck", models.FileField(blank=True, null=True, upload_to="onboarding/pitch_decks/")),
                ("business_model", models.CharField(blank=True, default="", max_length=100)),
                ("target_market", models.TextField(blank=True, default="")),
                ("revenue_model", models.TextField(blank=True, default="")),
                ("traction", models.TextField(blank=True, default="")),
                ("competitors", models.TextField(blank=True, default="")),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="founder_onboarding_data", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Founder Onboarding Data",
                "db_table": "onboarding_founder_data",
            },
        ),
        migrations.CreateModel(
            name="InvestorOnboardingData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("investor_type", models.CharField(blank=True, default="", max_length=50)),
                ("bio", models.TextField(blank=True, default="")),
                ("investment_focus", models.TextField(blank=True, default="")),
                ("preferred_industries", models.JSONField(blank=True, default=list)),
                ("preferred_stages", models.JSONField(blank=True, default=list)),
                ("ticket_size_min", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("ticket_size_max", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ("preferred_geographies", models.JSONField(blank=True, default=list)),
                ("linkedin_url", models.URLField(blank=True, default="")),
                ("website_url", models.URLField(blank=True, default="")),
                ("years_experience", models.PositiveIntegerField(blank=True, null=True)),
                ("portfolio_companies", models.JSONField(blank=True, default=list)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="investor_onboarding_data", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Investor Onboarding Data",
                "db_table": "onboarding_investor_data",
            },
        ),
    ]
