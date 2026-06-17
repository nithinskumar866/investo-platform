from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class InvestorPreference(models.Model):
    class RiskAppetite(models.TextChoices):
        CONSERVATIVE = "conservative", "Conservative"
        MODERATE = "moderate", "Moderate"
        AGGRESSIVE = "aggressive", "Aggressive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investor_preferences",
    )
    preferred_industries = models.JSONField(default=list, blank=True)
    preferred_stages = models.JSONField(default=list, blank=True)
    min_ticket_size = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    max_ticket_size = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    preferred_geographies = models.JSONField(default=list, blank=True)
    risk_appetite = models.CharField(
        max_length=20,
        choices=RiskAppetite.choices,
        default=RiskAppetite.MODERATE,
    )
    investment_focus = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "matching_investor_preference"

    def __str__(self):
        return f"Preferences: {self.user.email}"


class MatchScore(models.Model):
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_scores",
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        related_name="match_scores",
    )
    score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    details = models.JSONField(default=dict, blank=True)
    is_viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    is_bookmarked = models.BooleanField(default=False)
    bookmarked_at = models.DateTimeField(null=True, blank=True)
    is_contacted = models.BooleanField(default=False)
    contacted_at = models.DateTimeField(null=True, blank=True)
    is_ignored = models.BooleanField(default=False)
    ignored_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "matching_match_score"
        unique_together = [["investor", "startup"]]
        indexes = [
            models.Index(fields=["investor", "-score"]),
            models.Index(fields=["startup", "-score"]),
        ]

    def __str__(self):
        return f"{self.investor.email} ↔ {self.startup.name}: {self.score}%"


class InteractionEvent(models.Model):
    class EventType(models.TextChoices):
        VIEWED = "viewed", "Startup Viewed"
        BOOKMARKED = "bookmarked", "Startup Bookmarked"
        IGNORED = "ignored", "Startup Ignored"
        CONTACTED = "contacted", "Startup Contacted"
        SEARCHED = "searched", "Search Performed"
        SHARED = "shared", "Startup Shared"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interaction_events",
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        related_name="interaction_events",
        null=True,
        blank=True,
    )
    event_type = models.CharField(max_length=50, choices=EventType.choices, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    session_id = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "matching_interaction_event"
        indexes = [
            models.Index(fields=["user", "event_type"]),
            models.Index(fields=["startup", "event_type"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} {self.event_type} {self.startup}"
