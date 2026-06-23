import pytest
from decimal import Decimal
from django.utils import timezone
from rest_framework import status
from unittest.mock import patch

from apps.accounts.models import User
from apps.startups.models import Startup
from apps.investments.models import InvestmentOpportunity, InvestmentActivity
from apps.investments.services import InvestmentService
from apps.investments.serializers import (
    InvestmentOpportunityListSerializer,
    InvestmentOpportunityDetailSerializer,
)
from apps.common.exceptions import ApplicationError


# ── User fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="user@example.com", password="testpass123", role="entrepreneur",
    )


@pytest.fixture
def founder(db):
    return User.objects.create_user(
        email="founder@example.com", password="testpass123", role="entrepreneur",
        first_name="John", last_name="Doe",
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
        first_name="Jane", last_name="Smith",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123",
    )


@pytest.fixture
def startup(db, founder):
    return Startup.objects.create(
        owner=founder,
        name="Test Startup",
        slug="test-startup",
        industry="ai_ml",
        stage="seed",
        business_model="b2b",
        funding_goal=Decimal("1000000.00"),
        equity_offered=Decimal("10.00"),
        valuation=Decimal("5000000.00"),
        location="San Francisco",
        is_visible=True,
        status=Startup.Status.ACTIVE,
    )


@pytest.fixture
def opportunity(db, startup, investor):
    return InvestmentOpportunity.objects.create(
        startup=startup,
        investor=investor,
        amount_requested=Decimal("500000.00"),
        equity_requested=Decimal("10.00"),
        status=InvestmentOpportunity.Status.INTERESTED,
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestInvestmentOpportunityModel:
    def test_create_opportunity(self, opportunity):
        assert opportunity.pk is not None
        assert str(opportunity) == f"investor@example.com → Test Startup [interested]"
        assert opportunity.status == InvestmentOpportunity.Status.INTERESTED

    def test_status_choices(self):
        expected = [
            "interested", "meeting_scheduled", "due_diligence",
            "negotiating", "term_sheet_sent", "invested",
            "rejected", "withdrawn",
        ]
        assert sorted(c for c, _ in InvestmentOpportunity.Status.choices) == sorted(expected)

    def test_unique_together(self, opportunity, startup, investor):
        with pytest.raises(Exception):
            InvestmentOpportunity.objects.create(
                startup=startup, investor=investor,
            )

    def test_status_transition_allowed(self, opportunity):
        svc = InvestmentService
        assert svc._transition_allowed(
            InvestmentOpportunity.Status.INTERESTED,
            InvestmentOpportunity.Status.MEETING_SCHEDULED,
        )
        assert svc._transition_allowed(
            InvestmentOpportunity.Status.INTERESTED,
            InvestmentOpportunity.Status.REJECTED,
        )
        assert not svc._transition_allowed(
            InvestmentOpportunity.Status.INTERESTED,
            InvestmentOpportunity.Status.INVESTED,
        )
        assert not svc._transition_allowed(
            InvestmentOpportunity.Status.INVESTED,
            InvestmentOpportunity.Status.NEGOTIATING,
        )

    def test_terminal_states_have_no_transitions(self):
        svc = InvestmentService
        for terminal in ["invested", "rejected", "withdrawn"]:
            assert svc._transition_allowed(
                getattr(InvestmentOpportunity.Status, terminal.upper()),
                InvestmentOpportunity.Status.INTERESTED,
            ) == False


class TestInvestmentActivityModel:
    def test_create_activity(self, opportunity, investor):
        activity = InvestmentActivity.objects.create(
            opportunity=opportunity,
            actor=investor,
            action="created",
            metadata={"amount_requested": "500000.00"},
        )
        assert activity.pk is not None
        assert activity.action == "created"

    def test_activity_ordering(self, opportunity, investor):
        a1 = InvestmentActivity.objects.create(
            opportunity=opportunity, actor=investor, action="first",
        )
        a2 = InvestmentActivity.objects.create(
            opportunity=opportunity, actor=investor, action="second",
        )
        qs = InvestmentActivity.objects.all()
        assert qs.first() == a2


# ── Service tests ────────────────────────────────────────────────────────

class TestInvestmentService:
    def test_create_opportunity(self, startup, investor):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.create_opportunity(
                investor=investor,
                startup_id=startup.id,
                data={"amount_requested": "500000", "equity_requested": "10", "notes": ""},
            )
        assert opp.status == InvestmentOpportunity.Status.INTERESTED
        assert opp.investor == investor
        assert opp.startup == startup

    def test_create_duplicate_raises(self, opportunity, investor):
        with pytest.raises(ApplicationError, match="already exists"):
            with patch.multiple(
                "apps.investments.services",
                NotificationService=lambda **kw: None,
                ActivityFeedService=lambda **kw: None,
                RealtimeService=lambda **kw: None,
            ):
                InvestmentService.create_opportunity(
                    investor=investor,
                    startup_id=opportunity.startup_id,
                    data={},
                )

    def test_move_stage_valid(self, opportunity, investor):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.move_stage(
                opportunity.id, investor,
                InvestmentOpportunity.Status.MEETING_SCHEDULED,
            )
        assert opp.status == InvestmentOpportunity.Status.MEETING_SCHEDULED

    def test_move_stage_invalid(self, opportunity, investor):
        with pytest.raises(ApplicationError, match="Cannot move"):
            InvestmentService.move_stage(
                opportunity.id, investor,
                InvestmentOpportunity.Status.INVESTED,
            )

    def test_schedule_meeting(self, opportunity, investor):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.schedule_meeting(
                opportunity.id, investor,
                {"meeting_url": "http://meet.google.com/abc"},
            )
        assert opp.status == InvestmentOpportunity.Status.MEETING_SCHEDULED

    def test_schedule_meeting_wrong_state(self, opportunity, investor):
        opportunity.status = InvestmentOpportunity.Status.DUE_DILIGENCE
        opportunity.save()
        with pytest.raises(ApplicationError, match="Can only schedule"):
            InvestmentService.schedule_meeting(
                opportunity.id, investor, {},
            )

    def test_send_term_sheet(self, opportunity, investor):
        opportunity.status = InvestmentOpportunity.Status.NEGOTIATING
        opportunity.save()
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.send_term_sheet(
                opportunity.id, investor,
                {"amount_offered": "450000", "equity_offered": "8"},
            )
        assert opp.status == InvestmentOpportunity.Status.TERM_SHEET_SENT
        assert opp.amount_offered == Decimal("450000.00")

    def test_mark_invested(self, opportunity, investor):
        opportunity.status = InvestmentOpportunity.Status.TERM_SHEET_SENT
        opportunity.save()
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.mark_invested(
                opportunity.id, investor,
                {"amount_offered": "450000", "equity_offered": "8"},
            )
        assert opp.status == InvestmentOpportunity.Status.INVESTED
        assert opp.startup.status == "funded"

    def test_reject_deal(self, opportunity, investor):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.reject_deal(
                opportunity.id, investor, reason="Not a fit",
            )
        assert opp.status == InvestmentOpportunity.Status.REJECTED

    def test_withdraw_deal(self, opportunity, investor):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            opp = InvestmentService.withdraw_deal(
                opportunity.id, investor, reason="Changed mind",
            )
        assert opp.status == InvestmentOpportunity.Status.WITHDRAWN

    def test_reject_closed_deal_raises(self, opportunity, investor):
        opportunity.status = InvestmentOpportunity.Status.INVESTED
        opportunity.save()
        with pytest.raises(ApplicationError, match="already closed"):
            InvestmentService.reject_deal(opportunity.id, investor)

    def test_get_investor_dashboard(self, opportunity, investor):
        data = InvestmentService.get_investor_dashboard(investor)
        assert "total_deals" in data
        assert "active_deals" in data

    def test_get_startup_dashboard(self, opportunity, founder):
        data = InvestmentService.get_startup_dashboard(opportunity.startup, founder)
        assert "interested_investors" in data

    def test_list_investor_pipeline(self, opportunity, investor):
        qs = InvestmentService.list_investor_pipeline(investor)
        assert opportunity in qs

    def test_list_startup_pipeline(self, opportunity, founder):
        qs = InvestmentService.list_startup_pipeline(opportunity.startup_id, founder)
        assert opportunity in qs


# ── View tests ──────────────────────────────────────────────────────────

class TestInvestorPipelineViewSet:
    def test_list_pipeline(self, investor_client, opportunity):
        resp = investor_client.get("/api/v1/investments/pipeline/investor/")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data or "results" in data

    def test_create_opportunity(self, investor_client, startup):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                "/api/v1/investments/pipeline/investor/",
                {"startup_id": startup.id, "amount_requested": "500000"},
                format="json",
            )
        assert resp.status_code == 201

    def test_retrieve_opportunity(self, investor_client, opportunity):
        resp = investor_client.get(
            f"/api/v1/investments/pipeline/investor/{opportunity.id}/",
        )
        assert resp.status_code == 200

    def test_move_stage(self, investor_client, opportunity):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/move_stage/",
                {"status": "meeting_scheduled"},
                format="json",
            )
        assert resp.status_code == 200

    def test_schedule_meeting(self, investor_client, opportunity):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/schedule_meeting/",
                {"meeting_url": "http://meet.google.com/abc"},
                format="json",
            )
        assert resp.status_code == 200

    def test_send_term_sheet(self, investor_client, opportunity):
        opportunity.status = InvestmentOpportunity.Status.NEGOTIATING
        opportunity.save()
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/send_term_sheet/",
                {"amount_offered": "450000"},
                format="json",
            )
        assert resp.status_code == 200

    def test_mark_invested(self, investor_client, opportunity):
        opportunity.status = InvestmentOpportunity.Status.TERM_SHEET_SENT
        opportunity.save()
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            ActivityFeedService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/mark_invested/",
                {"amount_offered": "450000"},
                format="json",
            )
        assert resp.status_code == 200

    def test_reject(self, investor_client, opportunity):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/reject/",
                {"reason": "Not a fit"},
                format="json",
            )
        assert resp.status_code == 200

    def test_withdraw(self, investor_client, opportunity):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = investor_client.post(
                f"/api/v1/investments/pipeline/investor/{opportunity.id}/withdraw/",
                {"reason": "Changed mind"},
                format="json",
            )
        assert resp.status_code == 200

    def test_analytics(self, investor_client):
        resp = investor_client.get(
            "/api/v1/investments/pipeline/investor/analytics/",
        )
        assert resp.status_code == 200

    def test_permission_investor_only(self, founder_client):
        resp = founder_client.get("/api/v1/investments/pipeline/investor/")
        assert resp.status_code == 403


class TestStartupPipelineViewSet:
    def test_list_startup_pipeline(self, founder_client, opportunity):
        resp = founder_client.get(
            f"/api/v1/investments/pipeline/startup/?startup_id={opportunity.startup_id}",
        )
        assert resp.status_code == 200

    def test_list_requires_startup_id(self, founder_client):
        resp = founder_client.get("/api/v1/investments/pipeline/startup/")
        assert resp.status_code == 400

    def test_retrieve(self, founder_client, opportunity):
        resp = founder_client.get(
            f"/api/v1/investments/pipeline/startup/{opportunity.id}/?startup_id={opportunity.startup_id}",
        )
        assert resp.status_code == 200

    def test_move_stage(self, founder_client, opportunity):
        with patch.multiple(
            "apps.investments.services",
            NotificationService=lambda **kw: None,
            RealtimeService=lambda **kw: None,
        ):
            resp = founder_client.post(
                f"/api/v1/investments/pipeline/startup/{opportunity.id}/move_stage/"
                f"?startup_id={opportunity.startup_id}",
                {"status": "due_diligence"},
                format="json",
            )
        assert resp.status_code == 200

    def test_reject(self, founder_client, opportunity):
        resp = founder_client.post(
            f"/api/v1/investments/pipeline/startup/{opportunity.id}/reject/"
            f"?startup_id={opportunity.startup_id}",
            {"reason": "Not interested"},
            format="json",
        )
        assert resp.status_code == 200

    def test_analytics(self, founder_client, opportunity):
        resp = founder_client.get(
            f"/api/v1/investments/pipeline/startup/analytics/"
            f"?startup_id={opportunity.startup_id}",
        )
        assert resp.status_code == 200

    def test_permission_entrepreneur_only(self, investor_client):
        resp = investor_client.get(
            f"/api/v1/investments/pipeline/startup/?startup_id=1",
        )
        assert resp.status_code == 403
