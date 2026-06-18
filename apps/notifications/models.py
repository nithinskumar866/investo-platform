from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        NEW_MATCH = "new_match", "New Match"
        MATCH_SAVED = "match_saved", "Match Saved"
        MESSAGE_RECEIVED = "message_received", "Message Received"
        DEAL_CREATED = "deal_created", "Deal Created"
        DEAL_STAGE_CHANGED = "deal_stage_changed", "Deal Stage Changed"
        TERM_SHEET_SENT = "term_sheet_sent", "Term Sheet Sent"
        INVESTMENT_CLOSED = "investment_closed", "Investment Closed"
        DOCUMENT_UPLOADED = "document_uploaded", "Document Uploaded"
        DOCUMENT_VIEWED = "document_viewed", "Document Viewed"
        ACCESS_GRANTED = "access_granted", "Access Granted"
        PROFILE_VIEWED = "profile_viewed", "Profile Viewed"
        SYSTEM = "system", "System"

    TYPE_GROUP_MAP = {
        "new_match": "matches",
        "match_saved": "matches",
        "message_received": "messages",
        "deal_created": "investments",
        "deal_stage_changed": "investments",
        "term_sheet_sent": "investments",
        "investment_closed": "investments",
        "document_uploaded": "documents",
        "document_viewed": "documents",
        "access_granted": "documents",
        "profile_viewed": "system",
        "system": "system",
    }

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="triggered_notifications",
    )
    notification_type = models.CharField(
        max_length=25,
        choices=Type.choices,
        default=Type.SYSTEM,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "-created_at"]),
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["recipient", "notification_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.recipient.email})"

    def category(self):
        return self.TYPE_GROUP_MAP.get(self.notification_type, "system")


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    in_app_enabled = models.BooleanField(default=True)

    matching_notifications = models.BooleanField(default=True)
    investment_notifications = models.BooleanField(default=True)
    chat_notifications = models.BooleanField(default=True)
    document_notifications = models.BooleanField(default=True)
    marketing_notifications = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_preference"

    def __str__(self):
        return f"Preferences for {self.user.email}"
