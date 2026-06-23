import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock

from apps.accounts.models import User
from apps.startups.models import Startup
from apps.analytics.services import AnalyticsService


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
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
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
        name="Analytics Startup",
        slug="analytics-startup",
        industry="ai_ml",
        stage="seed",
        business_model="b2b",
        status=Startup.Status.ACTIVE,
        is_visible=True,
    )


# ── Service tests ────────────────────────────────────────────────────────

class TestAnalyticsService:
    def test_growth_pct_positive(self):
        result = AnalyticsService._growth_pct(150, 100)
        assert result == 50.0

    def test_growth_pct_negative(self):
        result = AnalyticsService._growth_pct(50, 100)
        assert result == -50.0

    def test_growth_pct_zero_previous(self):
        result = AnalyticsService._growth_pct(100, 0)
        assert result == 100.0

    def test_growth_pct_both_zero(self):
        result = AnalyticsService._growth_pct(0, 0)
        assert result == 0.0

    def test_parse_dates_defaults(self):
        start, end = AnalyticsService._parse_dates()
        assert end == timezone.now().date()
        assert start == end - timedelta(days=90)

    def test_parse_dates_custom(self):
        start, end = AnalyticsService._parse_dates(
            timezone.now().date() - timedelta(days=30),
            timezone.now().date(),
        )
        assert (end - start).days == 30

    def test_previous_period(self):
        start = timezone.now().date() - timedelta(days=30)
        end = timezone.now().date()
        prev_start, prev_end = AnalyticsService._previous_period(start, end)
        assert (prev_end - prev_start).days == 29

    def test_founder_dashboard(self, startup, founder):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            startup_views_total=Mock(return_value=100),
            startup_views_unique_investors=Mock(return_value=10),
            match_count=Mock(return_value=20),
            match_avg_score=Mock(return_value=85.5),
            saved_investor_count=Mock(return_value=5),
            chat_messages_for_startup=Mock(return_value=50),
            chat_conversation_count=Mock(return_value=3),
            data_room_views=Mock(return_value=30),
            data_room_unique_viewers=Mock(return_value=8),
            meeting_completion_rate=Mock(return_value=0.75),
            funding_progress=Mock(return_value={"raised": "500000", "goal": "1000000"}),
        ):
            data = AnalyticsService.founder_dashboard(founder, startup.id)
        assert "kpi_cards" in data
        assert "funding_progress" in data
        assert data["kpi_cards"]["startup_views"]["value"] == 100
        assert data["kpi_cards"]["matches"]["value"] == 20

    def test_founder_dashboard_invalid_startup(self, founder):
        with pytest.raises(Exception):
            AnalyticsService.founder_dashboard(founder, 9999)

    def test_investor_dashboard(self, investor):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_matches_total=Mock(return_value=30),
            investor_saved_startups_count=Mock(return_value=15),
            investor_profile_views_total=Mock(return_value=25),
            investor_deal_pipeline=Mock(return_value={"total": 5, "by_status": {}}),
            investor_meeting_stats=Mock(return_value={"total": 3, "completion_rate": 0.8, "scheduled": 2, "confirmed": 1, "completed": 1, "cancelled": 0}),
            investor_success_metrics=Mock(return_value={"invested_deals": 2}),
            investor_activity_trends=Mock(return_value=[]),
            investor_response_rate=Mock(return_value=0.9),
            investor_sector_distribution=Mock(return_value=[]),
            investor_ticket_size_analytics=Mock(return_value={}),
        ):
            data = AnalyticsService.investor_dashboard(investor)
        assert "kpi_cards" in data
        assert "deal_pipeline" in data
        assert "meeting_stats" in data

    def test_founder_funnel(self, startup, founder):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            meeting_funnel=Mock(
                return_value={"scheduled": 10, "completed": 5},
            ),
            investment_funnel=Mock(
                return_value={"interested": 20, "invested": 2},
            ),
        ):
            data = AnalyticsService.founder_funnel(founder, startup.id)
        assert "meeting_funnel" in data
        assert "investment_funnel" in data

    def test_investor_funnel(self, investor):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_meeting_stats=Mock(return_value={"total": 10, "scheduled": 5, "confirmed": 3, "completed": 2, "cancelled": 1}),
            investor_deal_pipeline=Mock(return_value={"total": 8, "by_status": {"interested": 3, "meeting_scheduled": 2, "invested": 1}}),
        ):
            data = AnalyticsService.investor_funnel(investor)
        assert "meeting_funnel" in data
        assert "investment_pipeline_summary" in data

    def test_founder_charts(self, startup, founder):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            startup_views_over_time=Mock(return_value=[]),
            match_trends=Mock(return_value=[]),
            chat_messages_over_time=Mock(return_value=[]),
            data_room_views_over_time=Mock(return_value=[]),
            weekly_growth=Mock(return_value=[]),
            monthly_growth=Mock(return_value=[]),
        ):
            data = AnalyticsService.founder_charts(founder, startup.id)
        assert "daily_views" in data
        assert "daily_matches" in data

    def test_investor_charts(self, investor):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_matches_trend=Mock(return_value=[]),
            investor_profile_views_trend=Mock(return_value=[]),
            investor_sector_distribution=Mock(return_value=[]),
        ):
            data = AnalyticsService.investor_charts(investor)
        assert "daily_matches" in data
        assert "sector_distribution" in data

    def test_reports(self):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            platform_overview=Mock(return_value={"users": 100, "startups": 50}),
            platform_growth=Mock(return_value=[]),
            platform_top_startups=Mock(return_value=[]),
            platform_top_investors=Mock(return_value=[]),
        ):
            data = AnalyticsService.reports()
        assert "current_period" in data
        assert "overview" in data

    def test_validate_startup_owner(self, startup, founder):
        AnalyticsService._validate_startup_owner(founder, startup.id)

    def test_validate_startup_owner_fails(self, startup):
        with pytest.raises(Exception):
            AnalyticsService._validate_startup_owner(
                User(email="other@example.com"),
                startup.id,
            )


# ── View tests ──────────────────────────────────────────────────────────

class TestAnalyticsViews:
    def test_founder_dashboard(self, founder_client, startup):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            startup_views_total=Mock(return_value=100),
            startup_views_unique_investors=Mock(return_value=10),
            match_count=Mock(return_value=20),
            match_avg_score=Mock(return_value=85.5),
            saved_investor_count=Mock(return_value=5),
            chat_messages_for_startup=Mock(return_value=50),
            chat_conversation_count=Mock(return_value=3),
            data_room_views=Mock(return_value=30),
            data_room_unique_viewers=Mock(return_value=8),
            meeting_completion_rate=Mock(return_value=0.75),
            funding_progress=Mock(return_value={}),
        ):
            resp = founder_client.get(
                f"/api/v1/analytics/founder/dashboard/?startup_id={startup.id}",
            )
        assert resp.status_code == 200

    def test_investor_dashboard(self, investor_client):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_matches_total=Mock(return_value=30),
            investor_saved_startups_count=Mock(return_value=15),
            investor_profile_views_total=Mock(return_value=25),
            investor_deal_pipeline=Mock(return_value={"total": 5, "by_status": {}}),
            investor_meeting_stats=Mock(return_value={"total": 3, "completion_rate": 0.8, "scheduled": 2, "confirmed": 1, "completed": 1, "cancelled": 0}),
            investor_success_metrics=Mock(return_value={"invested_deals": 2}),
            investor_activity_trends=Mock(return_value=[]),
            investor_response_rate=Mock(return_value=0.9),
            investor_sector_distribution=Mock(return_value=[]),
            investor_ticket_size_analytics=Mock(return_value={}),
        ):
            resp = investor_client.get("/api/v1/analytics/investor/dashboard/")
        assert resp.status_code == 200

    def test_founder_dashboard_date_filter(self, founder_client, startup):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            startup_views_total=Mock(return_value=50),
            startup_views_unique_investors=Mock(return_value=5),
            match_count=Mock(return_value=10),
            match_avg_score=Mock(return_value=80.0),
            saved_investor_count=Mock(return_value=3),
            chat_messages_for_startup=Mock(return_value=20),
            chat_conversation_count=Mock(return_value=2),
            data_room_views=Mock(return_value=15),
            data_room_unique_viewers=Mock(return_value=4),
            meeting_completion_rate=Mock(return_value=0.5),
            funding_progress=Mock(return_value={}),
        ):
            resp = founder_client.get(
                f"/api/v1/analytics/founder/dashboard/?startup_id={startup.id}"
                f"&start_date=2024-01-01&end_date=2024-12-31",
            )
        assert resp.status_code == 200

    def test_investor_dashboard_date_filter(self, investor_client):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_matches_total=Mock(return_value=10),
            investor_saved_startups_count=Mock(return_value=5),
            investor_profile_views_total=Mock(return_value=10),
            investor_deal_pipeline=Mock(return_value={"total": 2, "by_status": {}}),
            investor_meeting_stats=Mock(return_value={"total": 1, "completion_rate": 1.0, "scheduled": 1, "confirmed": 0, "completed": 0, "cancelled": 0}),
            investor_success_metrics=Mock(return_value={"invested_deals": 1}),
            investor_activity_trends=Mock(return_value=[]),
            investor_response_rate=Mock(return_value=0.8),
            investor_sector_distribution=Mock(return_value=[]),
            investor_ticket_size_analytics=Mock(return_value={}),
        ):
            resp = investor_client.get(
                "/api/v1/analytics/investor/dashboard/"
                "?start_date=2024-01-01&end_date=2024-12-31",
            )
        assert resp.status_code == 200

    def test_founder_funnel(self, founder_client, startup):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            meeting_funnel=Mock(return_value={"scheduled": 5, "completed": 2}),
            investment_funnel=Mock(return_value={"interested": 10, "invested": 1}),
        ):
            resp = founder_client.get(
                f"/api/v1/analytics/founder/funnel/?startup_id={startup.id}",
            )
        assert resp.status_code == 200

    def test_investor_funnel(self, investor_client):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            investor_meeting_stats=Mock(return_value={"total": 5, "scheduled": 2, "confirmed": 1, "completed": 1, "cancelled": 0}),
            investor_deal_pipeline=Mock(return_value={"total": 3, "by_status": {"interested": 1, "invested": 1}}),
        ):
            resp = investor_client.get("/api/v1/analytics/investor/funnel/")
        assert resp.status_code == 200

    def test_reports(self, authenticated_client):
        with patch.multiple(
            "apps.analytics.repositories.AnalyticsRepository",
            platform_overview=Mock(return_value={"users": 100}),
            platform_growth=Mock(return_value=[]),
            platform_top_startups=Mock(return_value=[]),
            platform_top_investors=Mock(return_value=[]),
        ):
            resp = authenticated_client.get("/api/v1/analytics/reports/")
        assert resp.status_code == 200

    def test_analytics_requires_auth(self, api_client):
        resp = api_client.get("/api/v1/analytics/founder/dashboard/")
        assert resp.status_code == 401
