from django.conf import settings
from django.db import models


class SavedSearch(models.Model):
    class SearchType(models.TextChoices):
        STARTUPS = "startups", "Startups"
        INVESTORS = "investors", "Investors"
        FOUNDERS = "founders", "Founders"
        OPPORTUNITIES = "opportunities", "Opportunities"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_searches",
    )
    name = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=20,
        choices=SearchType.choices,
        db_index=True,
    )
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "search_saved"
        indexes = [
            models.Index(fields=["user", "search_type"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.search_type})"


class SearchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_history",
    )
    query = models.CharField(max_length=500)
    search_type = models.CharField(max_length=20, db_index=True)
    filters = models.JSONField(default=dict, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "search_history"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["query"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} searched '{self.query}' ({self.search_type})"


class SearchClickEvent(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="search_clicks",
    )
    result_type = models.CharField(max_length=30, db_index=True)
    result_id = models.PositiveIntegerField()
    query = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_click"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["result_type", "result_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} clicked {self.result_type}#{self.result_id}"
