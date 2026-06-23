from unittest.mock import patch, MagicMock

import pytest

from apps.matching.tasks import (
    generate_investor_matches_task,
    generate_startup_matches_task,
    refresh_all_matches_task,
)

pytestmark = pytest.mark.django_db


class TestGenerateInvestorMatchesTask:
    @patch("apps.matching.services.MatchingService")
    @patch("apps.matching.tasks.cache")
    def test_runs_successfully(self, mock_cache, mock_service, investor):
        mock_match = MagicMock()
        mock_match.id = 1
        mock_service.generate_matches_for_investor.return_value = [mock_match]

        result = generate_investor_matches_task(investor.id, limit=50)

        mock_service.generate_matches_for_investor.assert_called_once_with(
            investor, limit=50,
        )
        mock_cache.set.assert_called_once()
        assert result == [1]

    @patch("apps.matching.services.MatchingService")
    @patch("apps.matching.tasks.cache")
    def test_returns_empty_when_investor_not_found(self, mock_cache, mock_service):
        result = generate_investor_matches_task(99999)

        mock_service.generate_matches_for_investor.assert_not_called()
        assert result is None


class TestGenerateStartupMatchesTask:
    @patch("apps.matching.services.MatchingService")
    @patch("apps.matching.tasks.cache")
    def test_runs_successfully(self, mock_cache, mock_service, startup):
        mock_match = MagicMock()
        mock_match.id = 1
        mock_service.generate_matches_for_startup.return_value = [mock_match]

        result = generate_startup_matches_task(startup.id, limit=50)

        mock_service.generate_matches_for_startup.assert_called_once_with(
            startup, limit=50,
        )
        mock_cache.set.assert_called_once()
        assert result == [1]

    @patch("apps.matching.services.MatchingService")
    @patch("apps.matching.tasks.cache")
    def test_returns_empty_when_startup_not_found(self, mock_cache, mock_service):
        result = generate_startup_matches_task(99999)

        mock_service.generate_matches_for_startup.assert_not_called()
        assert result is None


class TestRefreshAllMatchesTask:
    @patch("apps.matching.tasks.generate_investor_matches_task.delay")
    @patch("apps.matching.models.InvestorPreference")
    def test_queues_tasks_for_all_active_investors(self, mock_pref_model, mock_delay):
        mock_pref_model.objects.filter.return_value.values_list.return_value = [1, 2, 3]

        refresh_all_matches_task()

        assert mock_delay.call_count == 3
        mock_delay.assert_any_call(1)
        mock_delay.assert_any_call(2)
        mock_delay.assert_any_call(3)

    @patch("apps.matching.tasks.generate_investor_matches_task.delay")
    @patch("apps.matching.models.InvestorPreference")
    def test_no_tasks_when_no_active_investors(self, mock_pref_model, mock_delay):
        mock_pref_model.objects.filter.return_value.values_list.return_value = []

        refresh_all_matches_task()

        mock_delay.assert_not_called()
