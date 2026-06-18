from django.db import transaction
from django.db.models import Count, Avg, Q
from django.utils import timezone

from .models import MatchInsight, MatchFeedback


class MatchInsightRepository:
    """Data access layer for match intelligence operations."""

    # ── Insights ──────────────────────────────────────────────────

    @staticmethod
    def create_insight(match, summary, strengths, risks, recommendations):
        insight, created = MatchInsight.objects.update_or_create(
            match=match,
            defaults={
                "summary": summary,
                "strengths": strengths,
                "risks": risks,
                "recommendations": recommendations,
            },
        )
        return insight

    @staticmethod
    def get_insight(match):
        return MatchInsight.objects.filter(match=match).first()

    @staticmethod
    def get_insight_by_match_id(match_id):
        return MatchInsight.objects.select_related(
            "match", "match__startup", "match__investor",
        ).filter(match_id=match_id).first()

    @staticmethod
    def has_insight(match):
        return MatchInsight.objects.filter(match=match).exists()

    # ── Feedback ──────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def save_feedback(user, match, rating, feedback=""):
        fb, created = MatchFeedback.objects.update_or_create(
            user=user,
            match=match,
            defaults={"rating": rating, "feedback": feedback},
        )
        return fb, created

    @staticmethod
    def get_feedback(match):
        return MatchFeedback.objects.filter(match=match).select_related("user")

    @staticmethod
    def get_user_feedback(user, match):
        return MatchFeedback.objects.filter(user=user, match=match).first()

    @staticmethod
    def has_feedback(user, match):
        return MatchFeedback.objects.filter(user=user, match=match).exists()

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        insights_count = MatchInsight.objects.count()
        feedback_qs = MatchFeedback.objects

        total_feedback = feedback_qs.count()
        avg_rating = feedback_qs.aggregate(avg=Avg("rating"))["avg"]
        rating_distribution = list(
            feedback_qs.values("rating").annotate(
                count=Count("id"),
            ).order_by("rating")
        )

        low_rated = list(
            feedback_qs.filter(rating__lte=2).values(
                "match__score_breakdown",
            )[:50]
        )

        return {
            "total_insights_generated": insights_count,
            "total_feedback_submitted": total_feedback,
            "average_rating": round(avg_rating, 2) if avg_rating else None,
            "rating_distribution": rating_distribution,
            "feedback_rate": round(
                total_feedback / insights_count * 100, 1,
            ) if insights_count else 0.0,
        }

    @staticmethod
    def get_pattern_analytics():
        """Analyze common mismatch reasons from low-scoring matches."""
        from apps.matching.models import MatchScore
        low_matches = MatchScore.objects.filter(score__lt=40)[:200]
        breakdown_fields = [
            "industry", "stage", "funding", "geography", "keywords",
            "startup_completeness", "investor_completeness",
        ]
        patterns = {f: {"count": 0, "avg_score": 0.0} for f in breakdown_fields}

        for m in low_matches:
            bd = m.score_breakdown or {}
            for f in breakdown_fields:
                if bd.get(f, 100) < 40:
                    patterns[f]["count"] += 1

        high_matches = MatchScore.objects.filter(score__gte=70)[:200]
        converters = {f: {"count": 0} for f in breakdown_fields}
        for m in high_matches:
            bd = m.score_breakdown or {}
            for f in breakdown_fields:
                if bd.get(f, 0) >= 70:
                    converters[f]["count"] += 1

        return {
            "most_common_mismatches": sorted(
                [{"factor": k, "occurrences": v["count"]}
                 for k, v in patterns.items()],
                key=lambda x: x["occurrences"], reverse=True,
            )[:5],
            "top_converting_patterns": sorted(
                [{"factor": k, "matches": v["count"]}
                 for k, v in converters.items()],
                key=lambda x: x["matches"], reverse=True,
            )[:5],
        }
