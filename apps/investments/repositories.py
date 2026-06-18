from django.db import transaction
from django.db.models import Count, Q, Sum, Avg, Prefetch

from .models import InvestmentOpportunity, InvestmentActivity


class InvestmentRepository:
    """Data access layer for investment pipeline operations."""

    # ── Pipeline queries ──────────────────────────────────────────

    @staticmethod
    def get_pipeline_for_investor(investor, status=None):
        qs = InvestmentOpportunity.objects.filter(
            investor=investor,
        ).select_related(
            "startup", "startup__metrics",
        ).prefetch_related(
            Prefetch(
                "activities",
                queryset=InvestmentActivity.objects.select_related("actor")[:5],
                to_attr="recent_activities",
            ),
        )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-updated_at")

    @staticmethod
    def get_pipeline_for_startup(startup, status=None):
        qs = InvestmentOpportunity.objects.filter(
            startup=startup,
        ).select_related(
            "investor", "investor__investor_profile",
        ).prefetch_related(
            Prefetch(
                "activities",
                queryset=InvestmentActivity.objects.select_related("actor")[:5],
                to_attr="recent_activities",
            ),
        )
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-updated_at")

    @staticmethod
    def get_by_status(status, user=None, role=None):
        qs = InvestmentOpportunity.objects.filter(status=status)
        if role == "investor" and user:
            qs = qs.filter(investor=user)
        elif role == "entrepreneur" and user:
            qs = qs.filter(startup__owner=user)
        return qs.select_related("startup", "investor")

    @staticmethod
    def get_active_deals(user, role=None):
        active_statuses = [
            InvestmentOpportunity.Status.INTERESTED,
            InvestmentOpportunity.Status.MEETING_SCHEDULED,
            InvestmentOpportunity.Status.DUE_DILIGENCE,
            InvestmentOpportunity.Status.NEGOTIATING,
            InvestmentOpportunity.Status.TERM_SHEET_SENT,
        ]
        qs = InvestmentOpportunity.objects.filter(status__in=active_statuses)
        if role == "investor":
            qs = qs.filter(investor=user)
        elif role == "entrepreneur":
            qs = qs.filter(startup__owner=user)
        return qs.select_related("startup", "investor").order_by("-updated_at")

    # ── CRUD ──────────────────────────────────────────────────────

    @staticmethod
    def get_opportunity(opportunity_id):
        return InvestmentOpportunity.objects.select_related(
            "startup", "startup__metrics", "investor", "investor__investor_profile",
        ).prefetch_related(
            Prefetch(
                "activities",
                queryset=InvestmentActivity.objects.select_related("actor"),
            ),
        ).filter(id=opportunity_id).first()

    @staticmethod
    def create_opportunity(startup, investor, data: dict):
        opportunity = InvestmentOpportunity.objects.create(
            startup=startup,
            investor=investor,
            amount_requested=data.get("amount_requested"),
            amount_offered=data.get("amount_offered"),
            equity_requested=data.get("equity_requested"),
            equity_offered=data.get("equity_offered"),
            valuation=data.get("valuation"),
            proposed_valuation=data.get("proposed_valuation"),
            notes=data.get("notes", ""),
            status=InvestmentOpportunity.Status.INTERESTED,
        )
        return opportunity

    @staticmethod
    def update_opportunity(opportunity, data: dict):
        for field, value in data.items():
            setattr(opportunity, field, value)
        opportunity.save()
        return opportunity

    @staticmethod
    def record_activity(opportunity, actor, action, metadata=None):
        return InvestmentActivity.objects.create(
            opportunity=opportunity,
            actor=actor,
            action=action,
            metadata=metadata or {},
        )

    @staticmethod
    def get_activity_log(opportunity):
        return InvestmentActivity.objects.filter(
            opportunity=opportunity,
        ).select_related("actor").order_by("-timestamp")

    # ── Analytics ─────────────────────────────────────────────────

    @staticmethod
    def get_investor_analytics(investor):
        qs = InvestmentOpportunity.objects.filter(investor=investor)
        invested = qs.filter(status=InvestmentOpportunity.Status.INVESTED)
        active = qs.filter(
            status__in=[
                InvestmentOpportunity.Status.INTERESTED,
                InvestmentOpportunity.Status.MEETING_SCHEDULED,
                InvestmentOpportunity.Status.DUE_DILIGENCE,
                InvestmentOpportunity.Status.NEGOTIATING,
                InvestmentOpportunity.Status.TERM_SHEET_SENT,
            ],
        )
        total = qs.count()
        invested_count = invested.count()

        return {
            "total_deals": total,
            "active_deals": active.count(),
            "invested_deals": invested_count,
            "rejected_deals": qs.filter(status=InvestmentOpportunity.Status.REJECTED).count(),
            "withdrawn_deals": qs.filter(status=InvestmentOpportunity.Status.WITHDRAWN).count(),
            "avg_ticket_size": invested.aggregate(avg=Avg("amount_offered"))["avg"],
            "total_invested": invested.aggregate(sum=Sum("amount_offered"))["sum"],
            "conversion_rate": round(
                (invested_count / total * 100) if total else 0, 1,
            ),
            "by_stage": dict(
                qs.values("status").annotate(count=Count("id"))
                .values_list("status", "count"),
            ),
        }

    @staticmethod
    def get_startup_analytics(startup):
        qs = InvestmentOpportunity.objects.filter(startup=startup)
        interested = qs.filter(
            status__in=[
                InvestmentOpportunity.Status.INTERESTED,
                InvestmentOpportunity.Status.MEETING_SCHEDULED,
                InvestmentOpportunity.Status.DUE_DILIGENCE,
                InvestmentOpportunity.Status.NEGOTIATING,
                InvestmentOpportunity.Status.TERM_SHEET_SENT,
            ],
        )
        invested = qs.filter(status=InvestmentOpportunity.Status.INVESTED)

        return {
            "interested_investors": interested.count(),
            "active_negotiations": qs.filter(
                status__in=[
                    InvestmentOpportunity.Status.NEGOTIATING,
                    InvestmentOpportunity.Status.TERM_SHEET_SENT,
                ],
            ).count(),
            "invested_deals": invested.count(),
            "funds_raised": invested.aggregate(sum=Sum("amount_offered"))["sum"],
            "pipeline_value": interested.aggregate(
                sum=Sum("amount_requested"),
            )["sum"],
            "total_offers": qs.count(),
            "by_stage": dict(
                qs.values("status").annotate(count=Count("id"))
                .values_list("status", "count"),
            ),
        }

    @staticmethod
    def get_pipeline_status_counts(investor):
        return dict(
            InvestmentOpportunity.objects.filter(investor=investor)
            .values("status")
            .annotate(count=Count("id"))
            .values_list("status", "count"),
        )
