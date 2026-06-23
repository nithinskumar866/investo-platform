import pytest
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError

pytestmark = pytest.mark.django_db

from apps.matching.models import (
    InvestorPreference, MatchScore, SavedMatch,
    DismissedMatch, InteractionEvent,
)


class TestInvestorPreference:
    def test_defaults(self, investor):
        pref = InvestorPreference.objects.create(user=investor)
        assert pref.preferred_industries == []
        assert pref.preferred_stages == []
        assert pref.preferred_geographies == []
        assert pref.risk_appetite == InvestorPreference.RiskAppetite.MODERATE
        assert pref.investment_focus == ""
        assert pref.is_active is True
        assert pref.min_ticket_size is None
        assert pref.max_ticket_size is None

    def test_str(self, investor_preference):
        assert str(investor_preference) == f"Preferences: {investor_preference.user.email}"


class TestMatchScore:
    def test_create_with_valid_score(self, investor, startup):
        score = MatchScore.objects.create(
            investor=investor,
            startup=startup,
            score=Decimal("75.00"),
        )
        assert score.score == Decimal("75.00")
        assert score.status == MatchScore.Status.RECOMMENDED
        assert score.score_breakdown == {}
        assert score.is_viewed is False

    def test_score_validation_min(self, investor, startup):
        with pytest.raises(ValidationError):
            match = MatchScore(
                investor=investor,
                startup=startup,
                score=Decimal("-1"),
            )
            match.full_clean()

    def test_score_validation_max(self, investor, startup):
        with pytest.raises(ValidationError):
            match = MatchScore(
                investor=investor,
                startup=startup,
                score=Decimal("101"),
            )
            match.full_clean()

    def test_unique_together(self, investor, startup):
        MatchScore.objects.create(
            investor=investor, startup=startup, score=Decimal("50"),
        )
        with pytest.raises(IntegrityError):
            MatchScore.objects.create(
                investor=investor, startup=startup, score=Decimal("60"),
            )

    def test_str(self, match_score):
        expected = f"{match_score.investor.email} ↔ {match_score.startup.name}: {match_score.score}%"
        assert str(match_score) == expected


class TestSavedMatch:
    def test_unique_constraint(self, investor, match_score):
        SavedMatch.objects.create(user=investor, match=match_score)
        with pytest.raises(IntegrityError):
            SavedMatch.objects.create(user=investor, match=match_score)

    def test_str(self, investor, match_score):
        saved = SavedMatch.objects.create(user=investor, match=match_score)
        assert str(saved) == f"{investor.email} saved match {match_score.id}"


class TestDismissedMatch:
    def test_unique_constraint(self, investor, match_score):
        DismissedMatch.objects.create(user=investor, match=match_score)
        with pytest.raises(IntegrityError):
            DismissedMatch.objects.create(user=investor, match=match_score)

    def test_str(self, investor, match_score):
        dismissed = DismissedMatch.objects.create(user=investor, match=match_score)
        assert str(dismissed) == f"{investor.email} dismissed match {match_score.id}"


class TestInteractionEvent:
    def test_valid_event_types(self, investor, startup):
        for event_type in ["viewed", "bookmarked", "ignored", "contacted", "searched", "shared"]:
            event = InteractionEvent.objects.create(
                user=investor,
                startup=startup,
                event_type=event_type,
            )
            assert event.event_type == event_type
            assert event.metadata == {}

    def test_default_metadata(self, investor):
        event = InteractionEvent.objects.create(
            user=investor,
            event_type="searched",
        )
        assert event.metadata == {}
        assert event.session_id == ""
        assert event.startup is None

    def test_str(self, investor, startup):
        event = InteractionEvent.objects.create(
            user=investor,
            startup=startup,
            event_type="viewed",
        )
        assert str(event) == f"{investor.email} viewed {startup}"
