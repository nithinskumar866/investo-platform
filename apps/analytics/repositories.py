from django.contrib.auth import get_user_model
from django.db.models import (
    Avg, Count, Max, Min, Q, Sum,
)
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek

from apps.chat.models import Conversation, Message
from apps.data_room.models import DocumentViewEvent
from apps.investments.models import InvestmentOpportunity
from apps.matching.models import InteractionEvent, MatchScore, SavedMatch
from apps.meetings.models import Meeting
from apps.startups.models import Startup

User = get_user_model()


class AnalyticsRepository:
    """Aggregated data queries for analytics dashboards.

    No business logic — pure ORM aggregations using annotations,
    Case/When, Trunc date functions, and conditional Count/Sum.
    """

    # ── Date-range helper ─────────────────────────────────────────

    @staticmethod
    def _date_filter(start_date=None, end_date=None, field="created_at"):
        kwargs = {}
        if start_date:
            kwargs[f"{field}__gte"] = start_date
        if end_date:
            kwargs[f"{field}__lte"] = end_date
        return kwargs

    # ═══════════════════════════════════════════════════════════════
    #  FOUNDER DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    # ── 1. Startup views over time ────────────────────────────────

    @staticmethod
    def startup_views_over_time(startup_id, start_date=None, end_date=None):
        q = Q(startup_id=startup_id, event_type="viewed")
        period_q = Q()
        if start_date:
            period_q &= Q(created_at__gte=start_date)
        if end_date:
            period_q &= Q(created_at__lte=end_date)
        rows = (
            InteractionEvent.objects
            .filter(q & period_q)
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    @staticmethod
    def startup_views_total(startup_id, start_date=None, end_date=None):
        q = Q(startup_id=startup_id, event_type="viewed")
        return (
            InteractionEvent.objects
            .filter(q, **AnalyticsRepository._date_filter(start_date, end_date))
            .count()
        )

    @staticmethod
    def startup_views_unique_investors(startup_id, start_date=None, end_date=None):
        q = Q(startup_id=startup_id, event_type="viewed")
        return (
            InteractionEvent.objects
            .filter(q, **AnalyticsRepository._date_filter(start_date, end_date))
            .values("user")
            .distinct()
            .count()
        )

    # ── 2. Match generation trends ────────────────────────────────

    @staticmethod
    def match_trends(startup_id, start_date=None, end_date=None):
        rows = (
            MatchScore.objects
            .filter(
                startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    @staticmethod
    def match_count(startup_id, start_date=None, end_date=None):
        return (
            MatchScore.objects
            .filter(
                startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .count()
        )

    @staticmethod
    def match_avg_score(startup_id, start_date=None, end_date=None):
        result = (
            MatchScore.objects
            .filter(
                startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .aggregate(avg_score=Avg("score"))
        )
        return result["avg_score"]

    # ── 3. Saved investor count ───────────────────────────────────

    @staticmethod
    def saved_investor_count(startup_id):
        return (
            SavedMatch.objects
            .filter(match__startup_id=startup_id)
            .count()
        )

    @staticmethod
    def saved_investors(startup_id):
        return list(
            SavedMatch.objects
            .filter(match__startup_id=startup_id)
            .select_related("user")
            .values("user__id", "user__email", "user__first_name", "user__last_name")
        )

    # ── 4. Chat engagement metrics ────────────────────────────────

    @staticmethod
    def chat_messages_for_startup(startup_id, start_date=None, end_date=None):
        conversations = Conversation.objects.filter(
            participants__user__startups__id=startup_id,
        ).values_list("id", flat=True)

        return (
            Message.objects
            .filter(
                conversation_id__in=conversations,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .exclude(message_type="system")
            .count()
        )

    @staticmethod
    def chat_messages_over_time(startup_id, start_date=None, end_date=None):
        conversations = Conversation.objects.filter(
            participants__user__startups__id=startup_id,
        ).values_list("id", flat=True)

        rows = (
            Message.objects
            .filter(
                conversation_id__in=conversations,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .exclude(message_type="system")
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    @staticmethod
    def chat_conversation_count(startup_id):
        return (
            Conversation.objects
            .filter(participants__user__startups__id=startup_id)
            .distinct()
            .count()
        )

    # ── 5. Data room document views ───────────────────────────────

    @staticmethod
    def data_room_views(startup_id, start_date=None, end_date=None):
        return (
            DocumentViewEvent.objects
            .filter(
                document__data_room__startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date, field="viewed_at"),
            )
            .count()
        )

    @staticmethod
    def data_room_views_over_time(startup_id, start_date=None, end_date=None):
        rows = (
            DocumentViewEvent.objects
            .filter(
                document__data_room__startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date, field="viewed_at"),
            )
            .annotate(date=TruncDay("viewed_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    @staticmethod
    def data_room_unique_viewers(startup_id, start_date=None, end_date=None):
        return (
            DocumentViewEvent.objects
            .filter(
                document__data_room__startup_id=startup_id,
                **AnalyticsRepository._date_filter(start_date, end_date, field="viewed_at"),
            )
            .values("investor")
            .distinct()
            .count()
        )

    # ── 6. Meeting conversion funnel ──────────────────────────────

    @staticmethod
    def meeting_funnel(startup_id, start_date=None, end_date=None):
        base = Meeting.objects.filter(startup_id=startup_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        return {
            "scheduled": base.filter(status="scheduled").count(),
            "confirmed": base.filter(status="confirmed").count(),
            "completed": base.filter(status="completed").count(),
            "cancelled": base.filter(status="cancelled").count(),
        }

    @staticmethod
    def meeting_completion_rate(startup_id, start_date=None, end_date=None):
        base = Meeting.objects.filter(startup_id=startup_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        total = base.count()
        if total == 0:
            return 0.0
        completed = base.filter(status="completed").count()
        return round((completed / total) * 100, 2)

    # ── 7. Investment pipeline funnel ─────────────────────────────

    @staticmethod
    def investment_funnel(startup_id, start_date=None, end_date=None):
        base = InvestmentOpportunity.objects.filter(startup_id=startup_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        statuses = dict(InvestmentOpportunity.Status.choices)
        funnel = {}
        for status_code, _ in statuses.items():
            funnel[status_code] = base.filter(status=status_code).count()
        return funnel

    @staticmethod
    def investment_total_raised(startup_id):
        result = (
            InvestmentOpportunity.objects
            .filter(startup_id=startup_id, status="invested")
            .aggregate(total=Sum("amount_offered"))
        )
        return result["total"] or 0

    # ── 8. Funding progress ───────────────────────────────────────

    @staticmethod
    def funding_progress(startup_id):
        try:
            startup = Startup.objects.get(id=startup_id)
        except Startup.DoesNotExist:
            return {"goal": 0, "raised": 0, "percentage": 0.0}

        goal = startup.funding_goal or 0
        raised = AnalyticsRepository.investment_total_raised(startup_id)
        pct = round((raised / goal * 100), 2) if goal > 0 else 0.0
        return {"goal": float(goal), "raised": float(raised), "percentage": pct}

    # ── 9. Weekly/Monthly growth charts ───────────────────────────

    @staticmethod
    def weekly_growth(startup_id, start_date=None, end_date=None):
        def _count(qs):
            rows = (
                qs.annotate(week=TruncWeek("created_at"))
                .values("week")
                .annotate(count=Count("id"))
                .order_by("week")
            )
            return list(rows)

        interactions = InteractionEvent.objects.filter(
            startup_id=startup_id, event_type="viewed",
        )
        matches = MatchScore.objects.filter(startup_id=startup_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            interactions = interactions.filter(**df)
            matches = matches.filter(**df)

        return {
            "views": _count(interactions),
            "matches": _count(matches),
        }

    @staticmethod
    def monthly_growth(startup_id, start_date=None, end_date=None):
        def _count(qs):
            rows = (
                qs.annotate(month=TruncMonth("created_at"))
                .values("month")
                .annotate(count=Count("id"))
                .order_by("month")
            )
            return list(rows)

        interactions = InteractionEvent.objects.filter(
            startup_id=startup_id, event_type="viewed",
        )
        matches = MatchScore.objects.filter(startup_id=startup_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            interactions = interactions.filter(**df)
            matches = matches.filter(**df)

        return {
            "views": _count(interactions),
            "matches": _count(matches),
        }

    # ═══════════════════════════════════════════════════════════════
    #  INVESTOR DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    # ── 1. Matches generated ──────────────────────────────────────

    @staticmethod
    def investor_matches_total(investor_id, start_date=None, end_date=None):
        return (
            MatchScore.objects
            .filter(
                investor_id=investor_id,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .count()
        )

    @staticmethod
    def investor_matches_trend(investor_id, start_date=None, end_date=None):
        rows = (
            MatchScore.objects
            .filter(
                investor_id=investor_id,
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    @staticmethod
    def investor_matches_breakdown(investor_id):
        return (
            MatchScore.objects
            .filter(investor_id=investor_id)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

    # ── 2. Saved startups ─────────────────────────────────────────

    @staticmethod
    def investor_saved_startups_count(investor_id):
        return (
            SavedMatch.objects
            .filter(user_id=investor_id)
            .count()
        )

    @staticmethod
    def investor_saved_startups(investor_id):
        return list(
            SavedMatch.objects
            .filter(user_id=investor_id)
            .select_related("match__startup")
            .values("match__startup__id", "match__startup__name", "match__startup__industry")
        )

    # ── 3. Startup profile views ──────────────────────────────────

    @staticmethod
    def investor_profile_views_total(investor_id, start_date=None, end_date=None):
        return (
            InteractionEvent.objects
            .filter(
                user_id=investor_id,
                event_type="viewed",
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .count()
        )

    @staticmethod
    def investor_profile_views_trend(investor_id, start_date=None, end_date=None):
        rows = (
            InteractionEvent.objects
            .filter(
                user_id=investor_id,
                event_type="viewed",
                **AnalyticsRepository._date_filter(start_date, end_date),
            )
            .annotate(date=TruncDay("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        return list(rows)

    # ── 4. Deal pipeline analytics ────────────────────────────────

    @staticmethod
    def investor_deal_pipeline(investor_id, start_date=None, end_date=None):
        base = InvestmentOpportunity.objects.filter(investor_id=investor_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        return {
            "total": base.count(),
            "by_status": dict(
                base.values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            ),
            "total_amount_requested": (
                base.aggregate(total=Sum("amount_requested"))["total"] or 0
            ),
            "total_amount_offered": (
                base.aggregate(total=Sum("amount_offered"))["total"] or 0
            ),
        }

    # ── 5. Meeting conversion rates ───────────────────────────────

    @staticmethod
    def investor_meeting_stats(investor_id, start_date=None, end_date=None):
        base = Meeting.objects.filter(investor_id=investor_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        total = base.count()
        completed = base.filter(status="completed").count()
        cancelled = base.filter(status="cancelled").count()
        confirmed = base.filter(status="confirmed").count()

        return {
            "total": total,
            "scheduled": base.filter(status="scheduled").count(),
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "completion_rate": round((completed / total * 100), 2) if total else 0.0,
            "confirmation_rate": round(((confirmed + completed) / total * 100), 2) if total else 0.0,
        }

    # ── 6. Sector distribution ────────────────────────────────────

    @staticmethod
    def investor_sector_distribution(investor_id):
        return list(
            MatchScore.objects
            .filter(investor_id=investor_id)
            .values("startup__industry")
            .annotate(count=Count("id"))
            .annotate(avg_score=Avg("score"))
            .order_by("-count")
        )

    # ── 7. Ticket size analytics ──────────────────────────────────

    @staticmethod
    def investor_ticket_size_analytics(investor_id):
        base = InvestmentOpportunity.objects.filter(investor_id=investor_id)
        return base.aggregate(
            min_requested=Min("amount_requested"),
            max_requested=Max("amount_requested"),
            avg_requested=Avg("amount_requested"),
            min_offered=Min("amount_offered"),
            max_offered=Max("amount_offered"),
            avg_offered=Avg("amount_offered"),
        )

    # ── 8. Investment success metrics ─────────────────────────────

    @staticmethod
    def investor_success_metrics(investor_id, start_date=None, end_date=None):
        base = InvestmentOpportunity.objects.filter(investor_id=investor_id)
        df = AnalyticsRepository._date_filter(start_date, end_date)
        if start_date or end_date:
            base = base.filter(**df)

        invested = base.filter(status="invested")
        return {
            "total_deals": base.count(),
            "invested_deals": invested.count(),
            "conversion_rate": round(
                (invested.count() / base.count() * 100), 2
            ) if base.count() else 0.0,
            "total_invested": invested.aggregate(total=Sum("amount_offered"))["total"] or 0,
            "total_requested": base.aggregate(total=Sum("amount_requested"))["total"] or 0,
            "avg_investment": invested.aggregate(avg=Avg("amount_offered"))["avg"] or 0,
        }

    # ── 9. Activity trends ────────────────────────────────────────

    @staticmethod
    def investor_activity_trends(investor_id, start_date=None, end_date=None):
        df = AnalyticsRepository._date_filter(start_date, end_date)

        views = InteractionEvent.objects.filter(
            user_id=investor_id, event_type="viewed",
        )
        messages_sent = Message.objects.filter(sender_id=investor_id)
        matches = MatchScore.objects.filter(investor_id=investor_id)
        meetings = Meeting.objects.filter(
            Q(organizer_id=investor_id) | Q(investor_id=investor_id),
        )

        if start_date or end_date:
            views = views.filter(**df)
            messages_sent = messages_sent.filter(**df)
            matches = matches.filter(**df)
            meetings = meetings.filter(
                Q(created_at__gte=start_date, created_at__lte=end_date)
                if start_date and end_date
                else Q()
            )

        return {
            "profile_views": views.count(),
            "messages_sent": messages_sent.count(),
            "matches_generated": matches.count(),
            "meetings": meetings.count(),
        }

    # ── 10. Response rate analytics ───────────────────────────────

    @staticmethod
    def investor_response_rate(investor_id, start_date=None, end_date=None):
        df = AnalyticsRepository._date_filter(start_date, end_date)

        messages_received = Message.objects.filter(
            conversation__participants__user_id=investor_id,
        ).exclude(sender_id=investor_id)

        responses = Message.objects.filter(
            sender_id=investor_id,
            conversation__participants__user_id=investor_id,
        )

        if start_date or end_date:
            messages_received = messages_received.filter(**df)
            responses = responses.filter(**df)

        received = messages_received.values("conversation").distinct().count()
        replied = responses.values("conversation").distinct().count()

        return {
            "conversations_with_messages": received,
            "conversations_replied": replied,
            "response_rate": round((replied / received * 100), 2) if received else 0.0,
        }

    # ═══════════════════════════════════════════════════════════════
    #  PLATFORM-WIDE / REPORTS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def platform_overview(start_date=None, end_date=None):
        df = AnalyticsRepository._date_filter(start_date, end_date)
        date_q = Q(**df) if start_date or end_date else Q()

        key_metrics = {}
        key_metrics["total_startups"] = Startup.objects.filter(date_q).count()
        key_metrics["total_matches"] = MatchScore.objects.filter(date_q).count()
        key_metrics["total_investments"] = InvestmentOpportunity.objects.filter(date_q).count()
        key_metrics["total_meetings"] = Meeting.objects.filter(date_q).count()
        key_metrics["total_messages"] = Message.objects.filter(date_q).exclude(message_type="system").count()
        key_metrics["total_views"] = InteractionEvent.objects.filter(
            Q(event_type="viewed") & date_q,
        ).count()

        return key_metrics

    @staticmethod
    def platform_growth(start_date=None, end_date=None):
        def _weekly(qs):
            return list(
                qs.annotate(week=TruncWeek("created_at"))
                .values("week")
                .annotate(count=Count("id"))
                .order_by("week")
            )

        df = AnalyticsRepository._date_filter(start_date, end_date)
        q_filtered = Q(**df) if start_date or end_date else Q()

        return {
            "startups": _weekly(Startup.objects.filter(q_filtered)),
            "matches": _weekly(MatchScore.objects.filter(q_filtered)),
            "investments": _weekly(InvestmentOpportunity.objects.filter(q_filtered)),
            "meetings": _weekly(Meeting.objects.filter(q_filtered)),
            "messages": _weekly(
                Message.objects.filter(q_filtered).exclude(message_type="system"),
            ),
        }

    @staticmethod
    def platform_top_startups(limit=10, start_date=None, end_date=None):
        df = AnalyticsRepository._date_filter(start_date, end_date)
        date_q = Q(**df) if start_date or end_date else Q()

        return list(
            Startup.objects
            .annotate(
                match_count=Count("match_scores", filter=date_q),
                view_count_annotated=Count(
                    "interaction_events",
                    filter=Q(interaction_events__event_type="viewed") & date_q,
                ),
            )
            .order_by("-match_count", "-view_count_annotated")[:limit]
            .values("id", "name", "industry", "stage", "match_count", "view_count_annotated")
        )

    @staticmethod
    def platform_top_investors(limit=10, start_date=None, end_date=None):
        df = AnalyticsRepository._date_filter(start_date, end_date)
        date_q = Q(**df) if start_date or end_date else Q()

        return list(
            User.objects
            .filter(role="investor")
            .annotate(
                match_count=Count("match_scores", filter=date_q),
                investment_count=Count("investment_opportunities", filter=date_q),
                meeting_count=Count("investor_meetings", filter=date_q),
            )
            .order_by("-match_count")[:limit]
            .values("id", "email", "match_count", "investment_count", "meeting_count")
        )



