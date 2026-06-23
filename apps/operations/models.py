from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        ADMIN_ACTION = "admin_action", "Admin Action"
        USER_BAN = "user_ban", "User Banned"
        USER_RESTORE = "user_restore", "User Restored"
        USER_SUSPEND = "user_suspend", "User Suspended"
        STARTUP_APPROVE = "startup_approve", "Startup Approved"
        STARTUP_REJECT = "startup_reject", "Startup Rejected"
        STARTUP_ARCHIVE = "startup_archive", "Startup Archived"
        STARTUP_FLAG = "startup_flag", "Startup Flagged"
        SUBSCRIPTION_CHANGE = "subscription_change", "Subscription Changed"
        DEAL_INTERVENTION = "deal_intervention", "Deal Intervention"
        TICKET_ACTION = "ticket_action", "Ticket Action"
        DOCUMENT_FLAG = "document_flag", "Document Flagged"
        VERIFICATION_CHANGE = "verification_change", "Verification Changed"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action_type = models.CharField(max_length=30, choices=ActionType.choices, db_index=True)
    target_type = models.CharField(max_length=50, blank=True, default="")
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_repr = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "ops_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["action_type", "-created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self):
        return f"{self.action_type} by {self.actor} at {self.created_at}"


class SupportTicket(models.Model):
    class Category(models.TextChoices):
        ACCOUNT = "account", "Account"
        BILLING = "billing", "Billing"
        TECHNICAL = "technical", "Technical"
        REPORT = "report", "Report User/Content"
        FEATURE = "feature", "Feature Request"
        OTHER = "other", "Other"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        WAITING_ON_USER = "waiting_on_user", "Waiting on User"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets",
    )
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    priority = models.CharField(max_length=15, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN, db_index=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ops_ticket"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["assigned_to", "status"]),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject}"


class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_messages",
    )
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Admin-only internal note")
    attachments = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "ops_ticket_message"
        ordering = ["created_at"]

    def __str__(self):
        return f"Message by {self.sender.email} on {self.ticket.subject}"
