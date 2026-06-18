from django.conf import settings
from django.db import models


class MatchInsight(models.Model):
    match = models.OneToOneField(
        "matching.MatchScore",
        on_delete=models.CASCADE,
        related_name="insight",
    )
    summary = models.TextField()
    strengths = models.JSONField(default=list, blank=True)
    risks = models.JSONField(default=list, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "match_intelligence_insight"
        ordering = ["-generated_at"]

    def __str__(self):
        return f"Insight for match {self.match_id}"


class MatchFeedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="match_feedbacks",
    )
    match = models.ForeignKey(
        "matching.MatchScore",
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )
    rating = models.PositiveSmallIntegerField()
    feedback = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "match_intelligence_feedback"
        unique_together = [["user", "match"]]
        indexes = [
            models.Index(fields=["match", "rating"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} rated match {self.match_id}: {self.rating}/5"
