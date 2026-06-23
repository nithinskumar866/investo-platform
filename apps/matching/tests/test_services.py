import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.utils import timezone

from apps.matching.models import MatchScore, SavedMatch, DismissedMatch, InteractionEvent
from apps.matching.services import MatchingService, ScoringEngine

pytestmark = pytest.mark.django_db


class TestScoringEngine:
    def test_calculate_returns_score_and_breakdown(self, investor_preference, startup, investor):
        score, breakdown = ScoringEngine.calculate(investor_preference, startup)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        assert isinstance(breakdown, dict)
        for key in ["industry", "stage", "funding", "geography", "keywords",
                     "startup_completeness", "investor_completeness",
                     "startup_activity", "investor_activity"]:
            assert key in breakdown


class TestMatchingServiceGenerateForInvestor:
    @patch("apps.matching.services.MatchingRepository")
    @patch("apps.matching.services.InvestorProfileRepository")
    @patch("apps.notifications.services.NotificationService")
    def test_returns_scored_matches(self, mock_notify, mock_investor_profile_repo,
                                    mock_repo, investor, startup, investor_preference):
        mock_repo.get_investor_by_user.return_value = investor_preference
        mock_repo.get_startups_for_investor.return_value = [startup]
        mock_repo.get_startup_activity_scores.return_value = {startup.id: 2}
        mock_repo.get_investor_activity_count.return_value = 1
        mock_repo.save_match_record.return_value = MatchScore(
            investor=investor, startup=startup, score=Decimal("75.50"),
            score_breakdown={},
        )

        results = MatchingService.generate_matches_for_investor(investor)

        assert len(results) == 1
        assert results[0].score == Decimal("75.50")
        mock_repo.save_match_record.assert_called_once()

    @patch("apps.matching.services.MatchingRepository")
    def test_returns_empty_when_no_preferences(self, mock_repo, investor):
        mock_repo.get_investor_by_user.return_value = None

        results = MatchingService.generate_matches_for_investor(investor)

        assert results == []


class TestMatchingServiceGenerateForStartup:
    @patch("apps.matching.services.MatchingRepository")
    @patch("apps.matching.services.InvestorProfileRepository")
    @patch("apps.notifications.services.NotificationService")
    def test_returns_scored_matches(self, mock_notify, mock_investor_profile_repo,
                                    mock_repo, startup, investor, investor_preference):
        mock_repo.get_active_investors.return_value = [investor_preference]
        mock_repo.get_investor_activity_scores.return_value = {investor.id: 1}
        mock_repo.get_startup_activity_count.return_value = 2
        mock_repo.save_match_record.return_value = MatchScore(
            investor=investor, startup=startup, score=Decimal("80.00"),
            score_breakdown={},
        )

        results = MatchingService.generate_matches_for_startup(startup)

        assert len(results) == 1
        assert results[0].score == Decimal("80.00")
        mock_repo.save_match_record.assert_called_once()


class TestMatchingServiceSaveAndDismiss:
    @patch("apps.matching.services.MatchingRepository")
    @patch("apps.notifications.services.NotificationService")
    def test_save_match_creates_saved_and_updates_status(self, mock_notify, mock_repo,
                                                          investor, match_score):
        result = MatchingService.save_match(investor, match_score)

        mock_repo.create_saved_match.assert_called_once_with(investor, match_score)
        mock_repo.update_match_status.assert_called_once_with(
            match_score, MatchScore.Status.SAVED,
        )

    @patch("apps.matching.services.MatchingRepository")
    @patch("apps.notifications.services.NotificationService")
    def test_dismiss_match_creates_dismissed_and_updates(self, mock_notify, mock_repo,
                                                          investor, match_score):
        result = MatchingService.dismiss_match(investor, match_score)

        mock_repo.create_dismissed_match.assert_called_once_with(investor, match_score)
        mock_repo.update_match_status.assert_called_once_with(
            match_score, MatchScore.Status.DISMISSED,
        )


class TestMatchingServiceRecordInteraction:
    @patch("apps.matching.services.MatchingRepository")
    def test_records_viewed_event(self, mock_repo, investor, startup):
        mock_event = MagicMock()
        mock_event.id = 1
        mock_event.event_type = "viewed"
        mock_repo.create_interaction_event.return_value = mock_event
        mock_repo.get_match_for_investor_startup.return_value = None

        event = MatchingService.record_interaction(
            user=investor,
            startup=startup,
            event_type="viewed",
        )

        assert event.event_type == "viewed"
        mock_repo.create_interaction_event.assert_called_once_with(
            user=investor, startup=startup,
            event_type="viewed", metadata={},
        )

    @patch("apps.matching.services.MatchingRepository")
    def test_records_event_without_startup(self, mock_repo, investor):
        mock_event = MagicMock()
        mock_event.id = 2
        mock_event.event_type = "searched"
        mock_repo.create_interaction_event.return_value = mock_event

        event = MatchingService.record_interaction(
            user=investor,
            startup=None,
            event_type="searched",
        )

        assert event.event_type == "searched"
        mock_repo.get_match_for_investor_startup.assert_not_called()


class TestMatchingServiceGetAnalytics:
    @patch("apps.matching.models.SavedMatch")
    @patch("apps.matching.services.MatchScore")
    def test_returns_stats(self, mock_match_score, mock_saved_match):
        mock_match_score.objects.count.return_value = 10
        mock_match_score.objects.aggregate.return_value = {"avg": 65.5}
        mock_match_score.objects.values.return_value.annotate.return_value.values_list.return_value = [
            ("recommended", 5), ("saved", 3), ("dismissed", 2),
        ]
        mock_saved_match.objects.count.return_value = 8

        analytics = MatchingService.get_match_analytics()

        assert analytics["total_matches"] == 10
        assert analytics["avg_score"] == 65.5
        assert analytics["by_status"] == {
            "recommended": 5, "saved": 3, "dismissed": 2,
        }
        assert analytics["total_saved"] == 8


class TestMatchingServiceGetSaved:
    @patch("apps.matching.services.MatchingRepository")
    def test_get_saved_matches_calls_repo(self, mock_repo, investor):
        mock_repo.get_saved_matches.return_value = []

        result = MatchingService.get_saved_matches(investor)

        mock_repo.get_saved_matches.assert_called_once_with(investor)
        assert result == []

    @patch("apps.matching.services.MatchingRepository")
    def test_get_dismissed_matches_calls_repo(self, mock_repo, investor):
        mock_repo.get_dismissed_matches.return_value = []

        result = MatchingService.get_dismissed_matches(investor)

        mock_repo.get_dismissed_matches.assert_called_once_with(investor)
        assert result == []
