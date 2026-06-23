from decimal import Decimal
from django.utils.text import slugify

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator

from apps.common.validators import (
    validate_image_extension,
    validate_image_size,
    validate_document_extension,
    validate_file_size,
)


class Startup(models.Model):
    class Industry(models.TextChoices):
        AI_ML = "ai_ml", "Artificial Intelligence / ML"
        FINTECH = "fintech", "Fintech"
        HEALTHTECH = "healthtech", "Healthtech"
        EDTECH = "edtech", "Edtech"
        SAAS = "saas", "SaaS / Cloud"
        ECOMMERCE = "ecommerce", "E-commerce"
        MARKETPLACE = "marketplace", "Marketplace"
        SOCIAL = "social", "Social Media"
        GAMING = "gaming", "Gaming"
        CLEANTECH = "cleantech", "Cleantech"
        BIOTECH = "biotech", "Biotech"
        BLOCKCHAIN = "blockchain", "Blockchain / Web3"
        REAL_ESTATE = "real_estate", "Real Estate / PropTech"
        TRANSPORT = "transport", "Transport / Mobility"
        FOOD_TECH = "food_tech", "Food Tech"
        TRAVEL = "travel", "Travel / Hospitality"
        CYBERSECURITY = "cybersecurity", "Cybersecurity"
        IOT = "iot", "IoT / Hardware"
        MEDIA = "media", "Media / Entertainment"
        OTHER = "other", "Other"

    class Stage(models.TextChoices):
        IDEA = "idea", "Idea / Concept"
        PRE_SEED = "pre_seed", "Pre-Seed"
        SEED = "seed", "Seed"
        SERIES_A = "series_a", "Series A"
        SERIES_B = "series_b", "Series B"
        SERIES_C = "series_c", "Series C+"
        GROWTH = "growth", "Growth Stage"

    class BusinessModel(models.TextChoices):
        B2B = "b2b", "B2B"
        B2C = "b2c", "B2C"
        B2B2C = "b2b2c", "B2B2C"
        MARKETPLACE = "marketplace", "Marketplace"
        SUBSCRIPTION = "subscription", "Subscription"
        FREEMIUM = "freemium", "Freemium"
        ADVERTISING = "advertising", "Advertising"
        HARDWARE = "hardware", "Hardware"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        FUNDED = "funded", "Funded"
        CLOSED = "closed", "Closed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="startups",
    )
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=280, unique=True, blank=True, db_index=True)
    tagline = models.CharField(max_length=500, blank=True, default="")
    short_description = models.CharField(max_length=500, blank=True, default="")
    description = models.TextField(blank=True, default="")
    detailed_pitch = models.TextField(blank=True, default="")
    industry = models.CharField(
        max_length=50,
        choices=Industry.choices,
        db_index=True,
    )
    stage = models.CharField(
        max_length=50,
        choices=Stage.choices,
        db_index=True,
    )
    business_model = models.CharField(
        max_length=50,
        choices=BusinessModel.choices,
        blank=True,
        default="",
    )
    funding_goal = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    min_funding = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    max_funding = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    equity_offered = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    valuation = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    currency = models.CharField(max_length=3, default="USD")
    location = models.CharField(max_length=255, blank=True, default="")
    website = models.URLField(blank=True, default="")
    logo = models.ImageField(
        upload_to="startups/logos/",
        blank=True, null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    pitch_deck = models.FileField(
        upload_to="startups/pitch_decks/",
        blank=True, null=True,
        validators=[validate_document_extension, validate_file_size],
    )
    founded_date = models.DateField(null=True, blank=True)
    team_size = models.PositiveIntegerField(null=True, blank=True)

    gallery_images = models.JSONField(default=list, blank=True)

    is_verified = models.BooleanField(default=False)
    verification_document = models.FileField(
        upload_to="startups/verification/",
        blank=True, null=True,
        validators=[validate_document_extension, validate_file_size],
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    is_visible = models.BooleanField(default=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    view_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "startups_startup"
        verbose_name = "Startup"
        verbose_name_plural = "Startups"
        indexes = [
            models.Index(fields=["industry", "stage"]),
            models.Index(fields=["status", "is_visible"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-view_count"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["industry", "status", "is_visible"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Startup.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


class StartupTeamMember(models.Model):
    startup = models.ForeignKey(
        Startup, on_delete=models.CASCADE, related_name="team_members",
    )
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    email = models.EmailField(blank=True, default="")
    linkedin_url = models.URLField(blank=True, default="")
    photo = models.ImageField(
        upload_to="startups/team/",
        blank=True, null=True,
        validators=[validate_image_extension, validate_image_size],
    )
    bio = models.TextField(blank=True, default="")
    is_founder = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "startups_team_member"
        ordering = ["order", "is_founder", "name"]

    def __str__(self):
        return f"{self.name} - {self.role} ({self.startup.name})"


class StartupSocialLink(models.Model):
    class Platform(models.TextChoices):
        LINKEDIN = "linkedin", "LinkedIn"
        TWITTER = "twitter", "Twitter / X"
        CRUNCHBASE = "crunchbase", "Crunchbase"
        ANGEL_LIST = "angel_list", "AngelList / Wellfound"
        GITHUB = "github", "GitHub"
        YOUTUBE = "youtube", "YouTube"
        PRODUCT_HUNT = "product_hunt", "Product Hunt"
        OTHER = "other", "Other"

    startup = models.ForeignKey(
        Startup, on_delete=models.CASCADE, related_name="social_links",
    )
    platform = models.CharField(max_length=50, choices=Platform.choices)
    url = models.URLField()

    class Meta:
        db_table = "startups_social_link"
        unique_together = [["startup", "platform"]]

    def __str__(self):
        return f"{self.platform}: {self.startup.name}"


class StartupDocument(models.Model):
    class DocumentType(models.TextChoices):
        PITCH_DECK = "pitch_deck", "Pitch Deck"
        BUSINESS_PLAN = "business_plan", "Business Plan"
        FINANCIAL_MODEL = "financial_model", "Financial Model"
        MARKET_ANALYSIS = "market_analysis", "Market Analysis"
        TERM_SHEET = "term_sheet", "Term Sheet"
        OTHER = "other", "Other"

    startup = models.ForeignKey(
        Startup, on_delete=models.CASCADE, related_name="documents",
    )
    name = models.CharField(max_length=255)
    file = models.FileField(
        upload_to="startups/documents/",
        validators=[FileExtensionValidator(
            allowed_extensions=[
                "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
                "txt", "csv", "md", "jpg", "jpeg", "png",
            ],
        )],
    )
    document_type = models.CharField(
        max_length=50, choices=DocumentType.choices, default=DocumentType.OTHER,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "startups_document"

    def __str__(self):
        return self.name


class StartupFundingRound(models.Model):
    startup = models.ForeignKey(
        Startup, on_delete=models.CASCADE, related_name="funding_rounds",
    )
    round_name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    investors = models.TextField(blank=True, default="")
    valuation = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "startups_funding_round"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.round_name} - {self.startup.name}"


class StartupMetric(models.Model):
    startup = models.OneToOneField(
        Startup, on_delete=models.CASCADE, related_name="metrics",
    )
    monthly_revenue = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    annual_revenue = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    revenue_growth_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    monthly_active_users = models.PositiveIntegerField(null=True, blank=True)
    total_users = models.PositiveIntegerField(null=True, blank=True)
    gross_margin_pct = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    burn_rate = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    runway_months = models.PositiveIntegerField(null=True, blank=True)
    traction_description = models.TextField(blank=True, default="")
    key_achievements = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "startups_metric"
        verbose_name = "Startup Metric"
        verbose_name_plural = "Startup Metrics"

    def __str__(self):
        return f"Metrics: {self.startup.name}"
