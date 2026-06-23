from django.conf import settings
from django.db import models


class OnboardingWizard(models.Model):
    class WizardType(models.TextChoices):
        FOUNDER = "founder", "Founder"
        INVESTOR = "investor", "Investor"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="onboarding_wizard",
    )
    wizard_type = models.CharField(
        max_length=20,
        choices=WizardType.choices,
    )
    current_step = models.CharField(max_length=100, blank=True, default="")
    is_complete = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "onboarding_wizard"
        verbose_name = "Onboarding Wizard"

    def __str__(self):
        return f"{self.wizard_type} wizard for {self.user.email}"


class OnboardingStep(models.Model):
    wizard = models.ForeignKey(
        OnboardingWizard,
        on_delete=models.CASCADE,
        related_name="steps",
    )
    step_key = models.CharField(max_length=100)
    step_label = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "onboarding_step"
        verbose_name = "Onboarding Step"
        ordering = ["id"]

    def __str__(self):
        return f"{self.step_key} ({'done' if self.is_completed else 'pending'})"


class FounderOnboardingData(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="founder_onboarding_data",
    )
    company_name = models.CharField(max_length=255, blank=True, default="")
    tagline = models.CharField(max_length=200, blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    funding_stage = models.CharField(max_length=50, blank=True, default="")
    website = models.URLField(blank=True, default="")
    linkedin = models.URLField(blank=True, default="")
    team_size = models.PositiveIntegerField(null=True, blank=True)
    pitch_deck = models.FileField(upload_to="onboarding/pitch_decks/", blank=True, null=True)
    business_model = models.CharField(max_length=100, blank=True, default="")
    target_market = models.TextField(blank=True, default="")
    revenue_model = models.TextField(blank=True, default="")
    traction = models.TextField(blank=True, default="")
    competitors = models.TextField(blank=True, default="")

    class Meta:
        db_table = "onboarding_founder_data"
        verbose_name = "Founder Onboarding Data"

    def __str__(self):
        return f"Founder data for {self.user.email}"


class InvestorOnboardingData(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investor_onboarding_data",
    )
    investor_type = models.CharField(max_length=50, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    investment_focus = models.TextField(blank=True, default="")
    preferred_industries = models.JSONField(default=list, blank=True)
    preferred_stages = models.JSONField(default=list, blank=True)
    ticket_size_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ticket_size_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_geographies = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(blank=True, default="")
    website_url = models.URLField(blank=True, default="")
    years_experience = models.PositiveIntegerField(null=True, blank=True)
    portfolio_companies = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "onboarding_investor_data"
        verbose_name = "Investor Onboarding Data"

    def __str__(self):
        return f"Investor data for {self.user.email}"
