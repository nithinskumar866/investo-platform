from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from apps.matching.models import (
    MatchScore, SavedMatch, DismissedMatch, InteractionEvent, InvestorPreference,
)
from conftest import assert_success_response, assert_error_response

pytestmark = pytest.mark.django_db

# URL names
MATCH_LIST = "investor-match-list"
MATCH_DETAIL = "investor-match-detail"
MATCH_SAVE = "investor-match-save"
MATCH_DISMISS = "investor-match-dismiss"
MATCH_SAVED = "investor-match-saved"
MATCH_DISMISSED = "investor-match-dismissed-list"

ENT_LIST = "entrepreneur-match-list"
ENT_DETAIL = "entrepreneur-match-detail"
ENT_SAVE = "entrepreneur-match-save"
ENT_DISMISS = "entrepreneur-match-dismiss"
ENT_SAVED = "entrepreneur-match-saved"
ENT_DISMISSED = "entrepreneur-match-dismissed-list"

MY_MATCHES = "matching-matches"
PREFERENCES = "matching-preferences"
INTERACT = "matching-interact"
HISTORY = "matching-history"
ANALYTICS = "matching-analytics"


# ── Investor MatchViewSet ────────────────────────────────────────

class TestInvestorMatchViewSetList:
    def test_investor_can_list_matches(self, investor_client, match_score):
        resp = investor_client.get(reverse(MATCH_LIST))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1

    def test_non_investor_gets_403(self, founder_client):
        resp = founder_client.get(reverse(MATCH_LIST))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_with_reload_param(self, investor_client):
        with patch("apps.matching.services.MatchingService.generate_matches_for_investor") as mock_gen:
            mock_gen.return_value = []
            resp = investor_client.get(reverse(MATCH_LIST), {"reload": "true"})
            assert_success_response(resp)
            mock_gen.assert_called_once()

    def test_with_async_reload(self, investor_client):
        with patch("apps.matching.tasks.generate_investor_matches_task") as mock_task:
            mock_task.delay.return_value = None
            resp = investor_client.get(reverse(MATCH_LIST),
                                       {"reload": "true", "async": "true"})
            assert_success_response(resp)
            mock_task.delay.assert_called_once()


class TestInvestorMatchViewSetDetail:
    def test_investor_can_get_detail(self, investor_client, match_score):
        resp = investor_client.get(reverse(MATCH_DETAIL, args=[match_score.id]))
        assert_success_response(resp)
        assert resp.json()["data"]["id"] == match_score.id

    def test_non_investor_gets_403(self, founder_client, match_score):
        resp = founder_client.get(reverse(MATCH_DETAIL, args=[match_score.id]))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestInvestorMatchViewSetSave:
    def test_save_match(self, investor_client, match_score):
        resp = investor_client.post(reverse(MATCH_SAVE, args=[match_score.id]))
        assert_success_response(resp, status_code=200)
        assert SavedMatch.objects.filter(
            user=match_score.investor, match=match_score,
        ).exists()

    def test_save_duplicate_is_idempotent(self, investor_client, match_score):
        SavedMatch.objects.create(user=match_score.investor, match=match_score)
        resp = investor_client.post(reverse(MATCH_SAVE, args=[match_score.id]))
        assert_success_response(resp)


class TestInvestorMatchViewSetDismiss:
    def test_dismiss_match(self, investor_client, match_score):
        resp = investor_client.post(reverse(MATCH_DISMISS, args=[match_score.id]))
        assert_success_response(resp)
        assert DismissedMatch.objects.filter(
            user=match_score.investor, match=match_score,
        ).exists()

    def test_dismiss_duplicate_is_idempotent(self, investor_client, match_score):
        DismissedMatch.objects.create(user=match_score.investor, match=match_score)
        resp = investor_client.post(reverse(MATCH_DISMISS, args=[match_score.id]))
        assert_success_response(resp)


class TestInvestorMatchViewSetSaved:
    def test_list_saved_matches(self, investor_client, investor, match_score):
        SavedMatch.objects.create(user=investor, match=match_score)
        resp = investor_client.get(reverse(MATCH_SAVED))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1

    def test_empty_when_no_saved(self, investor_client):
        resp = investor_client.get(reverse(MATCH_SAVED))
        assert_success_response(resp)
        assert resp.json()["data"] == []


class TestInvestorMatchViewSetDismissed:
    def test_list_dismissed_matches(self, investor_client, investor, match_score):
        DismissedMatch.objects.create(user=investor, match=match_score)
        resp = investor_client.get(reverse(MATCH_DISMISSED))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1

    def test_empty_when_no_dismissed(self, investor_client):
        resp = investor_client.get(reverse(MATCH_DISMISSED))
        assert_success_response(resp)
        assert resp.json()["data"] == []


# ── Entrepreneur MatchViewSet ────────────────────────────────────

class TestEntrepreneurMatchViewSetList:
    def test_entrepreneur_can_list_matches(self, founder_client, match_score):
        resp = founder_client.get(reverse(ENT_LIST))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1

    def test_non_entrepreneur_gets_403(self, investor_client):
        resp = investor_client.get(reverse(ENT_LIST))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestEntrepreneurMatchViewSetDetail:
    def test_entrepreneur_can_get_detail(self, founder_client, match_score):
        resp = founder_client.get(reverse(ENT_DETAIL, args=[match_score.id]))
        assert_success_response(resp)
        assert resp.json()["data"]["id"] == match_score.id

    def test_non_entrepreneur_gets_403(self, investor_client, match_score):
        resp = investor_client.get(reverse(ENT_DETAIL, args=[match_score.id]))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


class TestEntrepreneurMatchViewSetSave:
    def test_save(self, founder_client, match_score, founder):
        resp = founder_client.post(reverse(ENT_SAVE, args=[match_score.id]))
        assert_success_response(resp)
        assert SavedMatch.objects.filter(user=founder, match=match_score).exists()


class TestEntrepreneurMatchViewSetDismiss:
    def test_dismiss(self, founder_client, match_score, founder):
        resp = founder_client.post(reverse(ENT_DISMISS, args=[match_score.id]))
        assert_success_response(resp)
        assert DismissedMatch.objects.filter(user=founder, match=match_score).exists()


class TestEntrepreneurMatchViewSetSaved:
    def test_list(self, founder_client, founder, match_score):
        SavedMatch.objects.create(user=founder, match=match_score)
        resp = founder_client.get(reverse(ENT_SAVED))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1


class TestEntrepreneurMatchViewSetDismissed:
    def test_list(self, founder_client, founder, match_score):
        DismissedMatch.objects.create(user=founder, match=match_score)
        resp = founder_client.get(reverse(ENT_DISMISSED))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1


# ── Legacy Endpoints ─────────────────────────────────────────────

class TestMyMatches:
    def test_investor_gets_matches(self, investor_client, match_score):
        resp = investor_client.get(reverse(MY_MATCHES))
        assert_success_response(resp)

    def test_entrepreneur_gets_matches(self, founder_client, match_score):
        resp = founder_client.get(reverse(MY_MATCHES))
        assert_success_response(resp)

    def test_non_investor_entrepreneur_gets_403(self, api_client, user):
        from conftest import auth_header
        resp = api_client.get(reverse(MY_MATCHES), **auth_header(user))
        assert_error_response(resp, status_code=403, error_code="WRONG_ROLE")


class TestInvestorPreferences:
    def test_get_preferences(self, investor_client, investor_preference):
        resp = investor_client.get(reverse(PREFERENCES))
        assert_success_response(resp)
        assert resp.json()["data"]["risk_appetite"] == "moderate"

    def test_non_investor_gets_403(self, founder_client):
        resp = founder_client.get(reverse(PREFERENCES))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_patch_preferences(self, investor_client):
        resp = investor_client.patch(
            reverse(PREFERENCES),
            {"risk_appetite": "aggressive"},
            format="json",
        )
        assert_success_response(resp)
        assert resp.json()["data"]["risk_appetite"] == "aggressive"


class TestInteract:
    def test_record_viewed(self, investor_client, startup):
        resp = investor_client.post(
            reverse(INTERACT),
            {"event_type": "viewed", "startup_id": startup.id},
            format="json",
        )
        assert_success_response(resp, status_code=201)
        assert InteractionEvent.objects.filter(
            user__email="investor@example.com", event_type="viewed",
        ).exists()

    def test_invalid_event_type(self, investor_client):
        resp = investor_client.post(
            reverse(INTERACT),
            {"event_type": "invalid_event"},
            format="json",
        )
        assert_error_response(resp, status_code=400, error_code="INVALID_EVENT_TYPE")

    def test_missing_startup_returns_404(self, investor_client):
        resp = investor_client.post(
            reverse(INTERACT),
            {"event_type": "viewed", "startup_id": 99999},
            format="json",
        )
        assert_error_response(resp, status_code=404, error_code="NOT_FOUND")


class TestInteractionHistory:
    def test_returns_events(self, investor_client, investor, startup):
        InteractionEvent.objects.create(
            user=investor, startup=startup, event_type="viewed",
        )
        resp = investor_client.get(reverse(HISTORY))
        assert_success_response(resp)
        assert len(resp.json()["data"]) == 1

    def test_empty_when_no_events(self, investor_client):
        resp = investor_client.get(reverse(HISTORY))
        assert_success_response(resp)
        assert resp.json()["data"] == []


class TestMatchAnalytics:
    def test_admin_can_access(self, admin_client):
        resp = admin_client.get(reverse(ANALYTICS))
        assert_success_response(resp)
        assert "total_matches" in resp.json()["data"]

    def test_non_admin_gets_403(self, investor_client):
        resp = investor_client.get(reverse(ANALYTICS))
        assert_error_response(resp, status_code=403, error_code="FORBIDDEN")
