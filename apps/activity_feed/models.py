from django.conf import settings
from django.db import models


class ActivityFeed(models.Model):
    class ActivityType(models.TextChoices):
        STARTUP_CREATED = "startup_created", "Startup Created"
        STARTUP_PUBLISHED = "startup_published", "Startup Published"
        STARTUP_FUNDED = "startup_funded", "Startup Funded"
        PROFILE_UPDATED = "profile_updated", "Profile Updated"
        MATCH_CREATED = "match_created", "Match Created"
        MEETING_SCHEDULED = "meeting_scheduled", "Meeting Scheduled"
        MEETING_COMPLETED = "meeting_completed", "Meeting Completed"
        INVESTMENT_STARTED = "investment_started", "Investment Started"
        INVESTMENT_CLOSED = "investment_closed", "Investment Closed"
        DOCUMENT_UPLOADED = "document_uploaded", "Document Uploaded"
        MILESTONE_ADDED = "milestone_added", "Milestone Added"
        INVESTOR_JOINED = "investor_joined", "Investor Joined"
        FOUNDER_JOINED = "founder_joined", "Founder Joined"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        CONNECTIONS = "connections", "Connections"
        PRIVATE = "private", "Private"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_activities",
    )
    activity_type = models.CharField(
        max_length=25,
        choices=ActivityType.choices,
        db_index=True,
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="feed_activities",
    )
    investor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="investor_feed_activities",
    )
    target_object_id = models.PositiveIntegerField(null=True, blank=True)
    target_object_type = models.CharField(max_length=50, blank=True, default="")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    visibility = models.CharField(
        max_length=15,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "activity_feed_item"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["activity_type", "-created_at"]),
            models.Index(fields=["actor", "-created_at"]),
            models.Index(fields=["startup", "-created_at"]),
            models.Index(fields=["investor", "-created_at"]),
            models.Index(fields=["visibility", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.actor.email} - {self.activity_type}"


class FeedReaction(models.Model):
    REACTION_CHOICES = [
        ("like", "Like"),
        ("celebrate", "Celebrate"),
        ("support", "Support"),
        ("insightful", "Insightful"),
        ("curious", "Curious"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_reactions",
    )
    feed_item = models.ForeignKey(
        ActivityFeed,
        on_delete=models.CASCADE,
        related_name="reactions",
    )
    reaction_type = models.CharField(max_length=15, choices=REACTION_CHOICES, default="like")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_feed_reaction"
        unique_together = [["user", "feed_item", "reaction_type"]]
        indexes = [
            models.Index(fields=["feed_item", "reaction_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} {self.reaction_type}s feed {self.feed_item_id}"


class FeedBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_bookmarks",
    )
    feed_item = models.ForeignKey(
        ActivityFeed,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_feed_bookmark"
        unique_together = [["user", "feed_item"]]

    def __str__(self):
        return f"{self.user.email} bookmarked feed {self.feed_item_id}"


class FeedComment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feed_comments",
    )
    feed_item = models.ForeignKey(
        ActivityFeed,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField()
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="replies",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "activity_feed_comment"
        indexes = [
            models.Index(fields=["feed_item", "-created_at"]),
        ]
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.email} commented on feed {self.feed_item_id}"
