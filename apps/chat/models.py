from django.conf import settings
from django.db import models

from apps.common.validators import validate_file_size, validate_attachment_extension


class Conversation(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "chat_conversation"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation {self.id}"


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_participations",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_conversation_participant"
        unique_together = [["conversation", "user"]]
        indexes = [
            models.Index(fields=["user", "conversation"]),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.conversation.id}"


class Message(models.Model):
    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        FILE = "file", "File"
        IMAGE = "image", "Image"
        SYSTEM = "system", "System"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    message_type = models.CharField(
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    content = models.TextField(blank=True, default="")
    attachment = models.FileField(
        upload_to="chat/attachments/",
        blank=True,
        null=True,
        validators=[validate_attachment_extension, validate_file_size],
    )
    metadata = models.JSONField(default=dict, blank=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message"
        indexes = [
            models.Index(fields=["conversation", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"


class MessageReadStatus(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="read_by",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_read_statuses",
    )
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_message_read_status"
        unique_together = [["message", "user"]]
        indexes = [
            models.Index(fields=["user", "read_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} read {self.message.id}"
