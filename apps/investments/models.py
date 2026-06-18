from django.conf import settings
from django.db import models


class InvestmentOpportunity(models.Model):
    class Status(models.TextChoices):
        INTERESTED = "interested", "Interested"
        MEETING_SCHEDULED = "meeting_scheduled", "Meeting Scheduled"
        DUE_DILIGENCE = "due_diligence", "Due Diligence"
        NEGOTIATING = "negotiating", "Negotiating"
        TERM_SHEET_SENT = "term_sheet_sent", "Term Sheet Sent"
        INVESTED = "invested", "Invested"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        related_name="investment_opportunities",
    )
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investment_opportunities",
    )
    amount_requested = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    amount_offered = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    equity_requested = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    equity_offered = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
    )
    valuation = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    proposed_valuation = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INTERESTED,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    term_sheet_url = models.URLField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "investments_opportunity"
        unique_together = [["startup", "investor"]]
        indexes = [
            models.Index(fields=["investor", "status"]),
            models.Index(fields=["startup", "status"]),
            models.Index(fields=["investor", "-created_at"]),
            models.Index(fields=["startup", "-created_at"]),
            models.Index(fields=["status", "-updated_at"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.investor.email} → {self.startup.name} [{self.status}]"


class InvestmentActivity(models.Model):
    opportunity = models.ForeignKey(
        InvestmentOpportunity,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="investment_activities",
    )
    action = models.CharField(max_length=50, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "investments_activity"
        indexes = [
            models.Index(fields=["opportunity", "-timestamp"]),
            models.Index(fields=["actor", "-timestamp"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.actor.email if self.actor else 'system'} {self.action} on {self.opportunity.id}"
