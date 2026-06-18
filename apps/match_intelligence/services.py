import logging
from django.conf import settings
from django.utils.module_loading import import_string

from apps.common.exceptions import ApplicationError

from .models import MatchInsight
from .repositories import MatchInsightRepository

logger = logging.getLogger(__name__)


def _get_ai_provider():
    """Load AI provider class from settings, falling back to RuleBasedProvider."""
    provider_path = getattr(
        settings, "MATCH_AI_PROVIDER",
        "apps.match_intelligence.providers.RuleBasedProvider",
    )
    try:
        provider_cls = import_string(provider_path)
        return provider_cls()
    except Exception as e:
        from .providers import RuleBasedProvider
        logger.warning(f"Failed to load AI provider {provider_path}: {e}. Falling back to RuleBasedProvider.")
        return RuleBasedProvider()


class MatchIntelligenceService:
    """Business logic for match intelligence operations."""

    # ── Explanation generation ────────────────────────────────────

    @classmethod
    def generate_match_explanation(cls, match):
        """Generate or retrieve cached explanation for a match."""
        existing = MatchInsightRepository.get_insight(match)
        if existing:
            return existing

        provider = _get_ai_provider()
        explanation = provider.generate_explanation(match)

        insight = MatchInsightRepository.create_insight(
            match=match,
            summary=explanation.summary,
            strengths=explanation.strengths,
            risks=explanation.risks,
            recommendations=explanation.recommendations,
        )
        logger.info(
            f"Generated insight for match {match.id} "
            f"({len(explanation.strengths)} strengths, "
            f"{len(explanation.risks)} risks)",
        )
        return insight

    @classmethod
    def get_explanation(cls, match_id, user):
        """Get explanation for a match, generating if needed."""
        from apps.matching.models import MatchScore
        match = MatchScore.objects.filter(id=match_id).select_related(
            "startup", "investor",
        ).first()

        if not match:
            raise ApplicationError("Match not found", "NOT_FOUND", 404)

        if match.investor_id != user.id and match.startup.owner_id != user.id:
            raise ApplicationError(
                "You do not have access to this match",
                "FORBIDDEN", 403,
            )

        return cls.generate_match_explanation(match)

    @classmethod
    def regenerate_explanation(cls, match_id, user):
        """Force-regenerate explanation, overwriting cached version."""
        from apps.matching.models import MatchScore
        match = MatchScore.objects.filter(id=match_id).first()
        if not match:
            raise ApplicationError("Match not found", "NOT_FOUND", 404)

        if match.investor_id != user.id and match.startup.owner_id != user.id:
            raise ApplicationError(
                "You do not have access to this match",
                "FORBIDDEN", 403,
            )

        if MatchInsightRepository.has_insight(match):
            MatchInsight.objects.filter(match=match).delete()

        return cls.generate_match_explanation(match)

    # ── Strengths, Risks, Recommendations (individual access) ─────

    @classmethod
    def get_strengths(cls, match_id, user):
        insight = cls.get_explanation(match_id, user)
        return insight.strengths

    @classmethod
    def get_risks(cls, match_id, user):
        insight = cls.get_explanation(match_id, user)
        return insight.risks

    @classmethod
    def get_recommendations(cls, match_id, user):
        insight = cls.get_explanation(match_id, user)
        return insight.recommendations

    # ── Feedback ──────────────────────────────────────────────────

    @staticmethod
    def collect_feedback(user, match_id, rating, feedback=""):
        from apps.matching.models import MatchScore
        match = MatchScore.objects.filter(id=match_id).first()

        if not match:
            raise ApplicationError("Match not found", "NOT_FOUND", 404)

        if match.investor_id != user.id and match.startup.owner_id != user.id:
            raise ApplicationError(
                "You can only provide feedback on your own matches",
                "FORBIDDEN", 403,
            )

        if rating < 1 or rating > 5:
            raise ApplicationError(
                "Rating must be between 1 and 5",
                "INVALID_RATING", 400,
            )

        fb, created = MatchInsightRepository.save_feedback(
            user, match, rating, feedback,
        )

        if not created:
            logger.info(
                f"Feedback updated for match {match_id} by {user.email}: "
                f"rating {rating}",
            )

        return fb

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_analytics():
        return MatchInsightRepository.get_analytics()

    @staticmethod
    def get_pattern_analytics():
        return MatchInsightRepository.get_pattern_analytics()

    # ── Scoring input improvement (AI feed) ───────────────────────

    @classmethod
    def improve_scoring_inputs(cls):
        """Generate insights to improve the matching algorithm.

        Analyses feedback patterns and low-rated matches to suggest
        weight adjustments for the ScoringEngine.
        """
        analytics = MatchInsightRepository.get_pattern_analytics()
        mismatches = analytics.get("most_common_mismatches", [])
        converters = analytics.get("top_converting_patterns", [])

        suggestions = []
        if mismatches:
            top_mismatch = mismatches[0]
            suggestions.append(
                f"Factor '{top_mismatch['factor']}' appears in "
                f"{top_mismatch['occurrences']} low-scoring matches. "
                "Consider reviewing its weight or matching logic."
            )

        if converters:
            top_converter = converters[0]
            suggestions.append(
                f"Factor '{top_converter['factor']}' correlates with "
                f"{top_converter['matches']} high-scoring matches. "
                "Weight may be appropriately high."
            )

        return suggestions
