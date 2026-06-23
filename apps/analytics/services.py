from datetime import date, timedelta

from django.utils import timezone

from apps.common.exceptions import ApplicationError
from apps.startups.models import Startup

from .repositories import AnalyticsRepository


class AnalyticsService:
    """Business logic for analytics dashboards.

    Composes repository data into dashboard payloads,
    computes trends, growth rates, and funnel conversions.
    """

    DEFAULT_DAYS = 90

    @classmethod
    def _parse_dates(cls, start_date=None, end_date=None):
        today = timezone.now().date()
        if end_date is None:
            end_date = today
        if start_date is None:
            start_date = today - timedelta(days=cls.DEFAULT_DAYS)
        return start_date, end_date

    @classmethod
    def _growth_pct(cls, current, previous):
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 2)

    @classmethod
    def _previous_period(cls, start_date, end_date):
        duration = (end_date - start_date).days
        return start_date - timedelta(days=duration), start_date - timedelta(days=1)

    # ═══════════════════════════════════════════════════════════════
    #  FOUNDER DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def founder_dashboard(cls, user, startup_id, start_date=None, end_date=None):
        cls._validate_startup_owner(user, startup_id)
        start_date, end_date = cls._parse_dates(start_date, end_date)
        prev_start, prev_end = cls._previous_period(start_date, end_date)

        views_total = AnalyticsRepository.startup_views_total(
            startup_id, start_date, end_date,
        )
        views_prev = AnalyticsRepository.startup_views_total(
            startup_id, prev_start, prev_end,
        )
        unique_investors = AnalyticsRepository.startup_views_unique_investors(
            startup_id, start_date, end_date,
        )
        match_count = AnalyticsRepository.match_count(
            startup_id, start_date, end_date,
        )
        match_prev = AnalyticsRepository.match_count(
            startup_id, prev_start, prev_end,
        )
        match_avg = AnalyticsRepository.match_avg_score(
            startup_id, start_date, end_date,
        )
        saved_count = AnalyticsRepository.saved_investor_count(startup_id)
        chat_count = AnalyticsRepository.chat_messages_for_startup(
            startup_id, start_date, end_date,
        )
        chat_prev = AnalyticsRepository.chat_messages_for_startup(
            startup_id, prev_start, prev_end,
        )
        conv_count = AnalyticsRepository.chat_conversation_count(startup_id)
        dr_views = AnalyticsRepository.data_room_views(
            startup_id, start_date, end_date,
        )
        dr_prev = AnalyticsRepository.data_room_views(
            startup_id, prev_start, prev_end,
        )
        dr_viewers = AnalyticsRepository.data_room_unique_viewers(
            startup_id, start_date, end_date,
        )
        meeting_rate = AnalyticsRepository.meeting_completion_rate(
            startup_id, start_date, end_date,
        )
        funding = AnalyticsRepository.funding_progress(startup_id)

        return {
            "kpi_cards": {
                "startup_views": {
                    "value": views_total,
                    "growth": cls._growth_pct(views_total, views_prev),
                    "unique_investors": unique_investors,
                },
                "matches": {
                    "value": match_count,
                    "growth": cls._growth_pct(match_count, match_prev),
                    "avg_score": match_avg,
                },
                "saved_by_investors": {
                    "value": saved_count,
                },
                "chat_engagement": {
                    "value": chat_count,
                    "growth": cls._growth_pct(chat_count, chat_prev),
                    "conversations": conv_count,
                },
                "data_room": {
                    "value": dr_views,
                    "growth": cls._growth_pct(dr_views, dr_prev),
                    "unique_viewers": dr_viewers,
                },
                "meeting_completion_rate": {
                    "value": meeting_rate,
                },
            },
            "funding_progress": funding,
        }

    @classmethod
    def founder_funnel(cls, user, startup_id):
        cls._validate_startup_owner(user, startup_id)

        meeting_funnel = AnalyticsRepository.meeting_funnel(startup_id)
        investment_funnel = AnalyticsRepository.investment_funnel(startup_id)

        m_total = sum(meeting_funnel.values()) or 1
        i_total = sum(investment_funnel.values()) or 1

        return {
            "meeting_funnel": {
                k: {"count": v, "pct": round((v / m_total) * 100, 1)}
                for k, v in meeting_funnel.items()
            },
            "investment_funnel": {
                k: {"count": v, "pct": round((v / i_total) * 100, 1)}
                for k, v in investment_funnel.items()
            },
        }

    @classmethod
    def founder_charts(cls, user, startup_id, start_date=None, end_date=None):
        cls._validate_startup_owner(user, startup_id)
        start_date, end_date = cls._parse_dates(start_date, end_date)

        views = AnalyticsRepository.startup_views_over_time(
            startup_id, start_date, end_date,
        )
        matches = AnalyticsRepository.match_trends(
            startup_id, start_date, end_date,
        )
        chat = AnalyticsRepository.chat_messages_over_time(
            startup_id, start_date, end_date,
        )
        dr = AnalyticsRepository.data_room_views_over_time(
            startup_id, start_date, end_date,
        )
        weekly = AnalyticsRepository.weekly_growth(startup_id, start_date, end_date)
        monthly = AnalyticsRepository.monthly_growth(startup_id, start_date, end_date)

        return {
            "daily_views": views,
            "daily_matches": matches,
            "daily_messages": chat,
            "daily_document_views": dr,
            "weekly_growth": weekly,
            "monthly_growth": monthly,
        }

    # ═══════════════════════════════════════════════════════════════
    #  INVESTOR DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def investor_dashboard(cls, user, start_date=None, end_date=None):
        start_date, end_date = cls._parse_dates(start_date, end_date)
        prev_start, prev_end = cls._previous_period(start_date, end_date)
        investor_id = user.id

        matches = AnalyticsRepository.investor_matches_total(
            investor_id, start_date, end_date,
        )
        matches_prev = AnalyticsRepository.investor_matches_total(
            investor_id, prev_start, prev_end,
        )
        saved = AnalyticsRepository.investor_saved_startups_count(investor_id)
        views = AnalyticsRepository.investor_profile_views_total(
            investor_id, start_date, end_date,
        )
        views_prev = AnalyticsRepository.investor_profile_views_total(
            investor_id, prev_start, prev_end,
        )
        pipeline = AnalyticsRepository.investor_deal_pipeline(
            investor_id, start_date, end_date,
        )
        meeting_stats = AnalyticsRepository.investor_meeting_stats(
            investor_id, start_date, end_date,
        )
        success = AnalyticsRepository.investor_success_metrics(
            investor_id, start_date, end_date,
        )
        activity = AnalyticsRepository.investor_activity_trends(
            investor_id, start_date, end_date,
        )
        response_rate = AnalyticsRepository.investor_response_rate(
            investor_id, start_date, end_date,
        )
        sector_dist = AnalyticsRepository.investor_sector_distribution(investor_id)
        ticket = AnalyticsRepository.investor_ticket_size_analytics(investor_id)

        return {
            "kpi_cards": {
                "matches": {
                    "value": matches,
                    "growth": cls._growth_pct(matches, matches_prev),
                },
                "saved_startups": {"value": saved},
                "profile_views": {
                    "value": views,
                    "growth": cls._growth_pct(views, views_prev),
                },
                "deal_pipeline_total": {"value": pipeline["total"]},
                "invested_deals": {"value": success["invested_deals"]},
                "meeting_completion_rate": {
                    "value": meeting_stats["completion_rate"],
                },
            },
            "deal_pipeline": pipeline,
            "meeting_stats": meeting_stats,
            "investment_success": success,
            "activity": activity,
            "response_rate": response_rate,
            "sector_distribution": sector_dist,
            "ticket_size": ticket,
        }

    @classmethod
    def investor_funnel(cls, user):
        investor_id = user.id
        meeting_stats = AnalyticsRepository.investor_meeting_stats(investor_id)
        pipeline = AnalyticsRepository.investor_deal_pipeline(investor_id)

        m_total = meeting_stats["total"] or 1
        return {
            "meeting_funnel": {
                "scheduled": {
                    "count": meeting_stats["scheduled"],
                    "pct": round((meeting_stats["scheduled"] / m_total) * 100, 1),
                },
                "confirmed": {
                    "count": meeting_stats["confirmed"],
                    "pct": round((meeting_stats["confirmed"] / m_total) * 100, 1),
                },
                "completed": {
                    "count": meeting_stats["completed"],
                    "pct": round((meeting_stats["completed"] / m_total) * 100, 1),
                },
                "cancelled": {
                    "count": meeting_stats["cancelled"],
                    "pct": round((meeting_stats["cancelled"] / m_total) * 100, 1),
                },
            },
            "investment_pipeline_summary": {
                "interested": pipeline["by_status"].get("interested", 0),
                "meeting_scheduled": pipeline["by_status"].get("meeting_scheduled", 0),
                "due_diligence": pipeline["by_status"].get("due_diligence", 0),
                "negotiating": pipeline["by_status"].get("negotiating", 0),
                "term_sheet_sent": pipeline["by_status"].get("term_sheet_sent", 0),
                "invested": pipeline["by_status"].get("invested", 0),
            },
        }

    @classmethod
    def investor_charts(cls, user, start_date=None, end_date=None):
        start_date, end_date = cls._parse_dates(start_date, end_date)
        investor_id = user.id

        matches_trend = AnalyticsRepository.investor_matches_trend(
            investor_id, start_date, end_date,
        )
        views_trend = AnalyticsRepository.investor_profile_views_trend(
            investor_id, start_date, end_date,
        )
        sector = AnalyticsRepository.investor_sector_distribution(investor_id)

        return {
            "daily_matches": matches_trend,
            "daily_views": views_trend,
            "sector_distribution": sector,
        }

    # ═══════════════════════════════════════════════════════════════
    #  PLATFORM REPORTS
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def reports(cls, start_date=None, end_date=None):
        start_date, end_date = cls._parse_dates(start_date, end_date)
        prev_start, prev_end = cls._previous_period(start_date, end_date)

        current = AnalyticsRepository.platform_overview(start_date, end_date)
        previous = AnalyticsRepository.platform_overview(prev_start, prev_end)
        growth = AnalyticsRepository.platform_growth(start_date, end_date)
        top_startups = AnalyticsRepository.platform_top_startups(
            start_date=start_date, end_date=end_date,
        )
        top_investors = AnalyticsRepository.platform_top_investors(
            start_date=start_date, end_date=end_date,
        )

        return {
            "current_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "overview": {
                metric: {"value": current[metric],
                         "growth": cls._growth_pct(current[metric], previous.get(metric, 0))}
                for metric in current
            },
            "growth_trends": growth,
            "top_startups": top_startups,
            "top_investors": top_investors,
        }

    # ═══════════════════════════════════════════════════════════════
    #  HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _validate_startup_owner(user, startup_id):
        if not Startup.objects.filter(id=startup_id, owner=user).exists():
            raise ApplicationError(
                "Startup not found or not owned by you",
                "NOT_FOUND", 404,
            )
