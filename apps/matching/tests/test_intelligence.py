import pytest
from django.db import IntegrityError

from apps.match_intelligence.models import MatchInsight, MatchFeedback

pytestmark = pytest.mark.django_db


class TestMatchInsight:
    def test_create(self, match_score):
        insight = MatchInsight.objects.create(
            match=match_score,
            summary="Strong alignment in AI/ML sector with similar growth trajectories",
            strengths=["Experienced team", "Growing market", "Proven traction"],
            risks=["Competitive landscape", "Capital intensive"],
            recommendations=["Lead the round", "Connect with strategic partners"],
        )
        assert insight.match_id == match_score.id
        assert insight.summary.startswith("Strong alignment")
        assert len(insight.strengths) == 3
        assert len(insight.risks) == 2
        assert len(insight.recommendations) == 2
        assert insight.generated_at is not None

    def test_one_to_one_with_match(self, match_score):
        MatchInsight.objects.create(match=match_score, summary="First insight")
        with pytest.raises(IntegrityError):
            MatchInsight.objects.create(match=match_score, summary="Second insight")

    def test_defaults(self, match_score):
        insight = MatchInsight.objects.create(
            match=match_score, summary="Test insight",
        )
        assert insight.strengths == []
        assert insight.risks == []
        assert insight.recommendations == []

    def test_str(self, match_score):
        insight = MatchInsight.objects.create(match=match_score, summary="Test")
        assert str(insight) == f"Insight for match {match_score.id}"


class TestMatchFeedback:
    def test_create(self, investor, match_score):
        fb = MatchFeedback.objects.create(
            user=investor,
            match=match_score,
            rating=4,
            feedback="Great match! Very aligned with my portfolio.",
        )
        assert fb.rating == 4
        assert fb.feedback != ""

    def test_unique_constraint(self, investor, match_score):
        MatchFeedback.objects.create(user=investor, match=match_score, rating=5)
        with pytest.raises(IntegrityError):
            MatchFeedback.objects.create(user=investor, match=match_score, rating=3)

    def test_default_feedback_empty(self, investor, match_score):
        fb = MatchFeedback.objects.create(
            user=investor, match=match_score, rating=3,
        )
        assert fb.feedback == ""

    def test_str(self, investor, match_score):
        fb = MatchFeedback.objects.create(
            user=investor, match=match_score, rating=4,
        )
        assert str(fb) == f"{investor.email} rated match {match_score.id}: 4/5"
