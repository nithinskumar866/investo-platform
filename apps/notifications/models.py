from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Type(models.TextChoices):
        MATCH = "match", "New Match"
        MESSAGE = "message", "New Message"
        STARTUP_UPDATE = "startup_update", "Startup Update"
        INVESTOR_INTEREST = "investor_interest", "Investor Interest"
        DOCUMENT_UPLOAD = "document_upload", "Document Upload"
        PROFILE_VIEW = "profile_view", "Profile View"
        BOOKMARK = "bookmark", "Bookmark"
        SYSTEM = "system", "System"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=50,
        choices=Type.choices,
        default=Type.OTHER,
        db_index=True,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=100, blank=True, default="")
    action_url = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
            models.Index(fields=["user", "notification_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.user.email})"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])