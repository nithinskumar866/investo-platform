from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """
    Custom User model replacing the old SignupDetail.

    Why AbstractUser instead of AbstractBaseUser:
    AbstractUser gives us username, first_name, last_name, is_staff,
    is_active, date_joined, and groups/permissions out of the box.
    We only need to add: role, avatar, phone, verification status.

    AbstractBaseUser would require reimplementing all of that from
    scratch — more code to maintain, more surface area for bugs.

    Why email is USERNAME_FIELD:
    Users remember their email, not a username. This matches the
    existing SignupDetail behavior and is more professional.

    Role field design:
    Stored as a CharField with choices rather than a separate table
    or permissions group. This is simpler and sufficient for 5 roles.
    Future: if roles need granular permissions, we layer Django's
    built-in permission system on top.
    """

    class Role(models.TextChoices):
        ENTREPRENEUR = "entrepreneur", "Entrepreneur"
        INVESTOR = "investor", "Investor"
        MENTOR = "mentor", "Mentor"
        TALENT = "talent", "Talent"
        ADMIN = "admin", "Admin"

    username = models.CharField(max_length=150, blank=True, default="")
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ENTREPRENEUR,
        db_index=True,
    )
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    is_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.email


class EntrepreneurProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="entrepreneur_profile"
    )
    company_name = models.CharField(max_length=255)
    company_description = models.TextField(blank=True, default="")
    tagline = models.CharField(max_length=200, blank=True, default="")
    website = models.URLField(blank=True, default="")
    industry = models.CharField(max_length=100, blank=True, default="")
    funding_stage = models.CharField(
        max_length=50,
        choices=[
            ("pre_seed", "Pre-Seed"),
            ("seed", "Seed"),
            ("series_a", "Series A"),
            ("series_b", "Series B"),
            ("series_c", "Series C+"),
            ("growth", "Growth"),
        ],
        blank=True,
        default="",
    )
    pitch_deck = models.FileField(upload_to="pitch_decks/", blank=True, null=True)
    linkedin_url = models.URLField(blank=True, default="")
    team_size = models.PositiveIntegerField(null=True, blank=True)
    achievements = models.TextField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    social_links = models.JSONField(default=dict, blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_entrepreneur_profile"
        verbose_name = "Entrepreneur Profile"
        indexes = [
            models.Index(fields=["is_public", "industry"]),
            models.Index(fields=["funding_stage"]),
        ]

    def __str__(self):
        return f"{self.company_name or self.user.email} ({self.user.email})"


class InvestorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="investor_profile"
    )
    investor_type = models.CharField(
        max_length=50,
        choices=[
            ("angel", "Angel Investor"),
            ("vc", "Venture Capital"),
            ("corporate", "Corporate VC"),
            ("accelerator", "Accelerator"),
            ("family_office", "Family Office"),
            ("fund", "Investment Fund"),
        ],
        blank=True,
        default="",
    )
    bio = models.TextField(blank=True, default="")
    tagline = models.CharField(max_length=200, blank=True, default="")
    investment_focus = models.TextField(blank=True, default="")
    preferred_industries = models.JSONField(default=list, blank=True)
    preferred_stages = models.JSONField(default=list, blank=True)
    ticket_size_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ticket_size_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    preferred_geographies = models.JSONField(default=list, blank=True)
    portfolio_companies = models.JSONField(default=list, blank=True)
    linkedin_url = models.URLField(blank=True, default="")
    website_url = models.URLField(blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)
    investments_completed = models.PositiveIntegerField(null=True, blank=True)
    lead_investor = models.BooleanField(default=False)
    follow_on_investor = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Deprecated fields kept for backward compatibility
    preferred_stage = models.CharField(
        max_length=50,
        choices=[
            ("pre_seed", "Pre-Seed"),
            ("seed", "Seed"),
            ("series_a", "Series A"),
            ("series_b", "Series B"),
            ("series_c", "Series C+"),
        ],
        blank=True,
        default="",
    )
    industries_of_interest = models.TextField(blank=True, default="")
    portfolio_count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "accounts_investor_profile"
        verbose_name = "Investor Profile"
        indexes = [
            models.Index(fields=["is_public", "investor_type"]),
            models.Index(fields=["city", "country"]),
            models.Index(fields=["years_of_experience"]),
        ]

    def __str__(self):
        return f"Investor {self.user.email} ({self.investor_type or 'no type'})"
