from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.investments.models import InvestmentOpportunity
from apps.matching.models import MatchScore
from apps.startups.models import Startup

from .models import AuditLog, SupportMessage, SupportTicket

User = get_user_model()


class DashboardRepository:
    """Aggregated data for admin dashboard KPI cards."""

    @staticmethod
    def platform_summary():
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        return {
            "total_users": User.objects.filter(is_active=True).count(),
            "total_founders": User.objects.filter(role="entrepreneur", is_active=True).count(),
            "total_investors": User.objects.filter(role="investor", is_active=True).count(),
            "active_subscriptions": User.objects.filter(
                subscription__status__in=["active", "trial"],
            ).count(),
            "total_startups": Startup.objects.count(),
            "active_deals": InvestmentOpportunity.objects.exclude(
                status__in=["rejected", "withdrawn", "invested"],
            ).count(),
            "closed_deals": InvestmentOpportunity.objects.filter(status="invested").count(),
            "new_matches_30d": MatchScore.objects.filter(
                created_at__gte=thirty_days_ago,
            ).count(),
            "open_tickets": SupportTicket.objects.exclude(
                status__in=["resolved", "closed"],
            ).count(),
        }


class UserManagementRepository:
    """Data access for admin user management."""

    @staticmethod
    def search_users(query, role=None, status=None, page=1, page_size=20):
        q = Q()
        if query:
            q &= Q(email__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        if role:
            q &= Q(role=role)
        if status == "active":
            q &= Q(is_active=True)
        elif status == "suspended":
            q &= Q(is_active=False)

        offset = (page - 1) * page_size
        return (
            User.objects.filter(q)
            .order_by("-date_joined")
            .select_related("entrepreneur_profile", "investor_profile")[offset:offset + page_size]
        )

    @staticmethod
    def get_user_detail(user_id):
        return User.objects.filter(id=user_id).select_related(
            "entrepreneur_profile", "investor_profile", "subscription__plan",
        ).first()

    @staticmethod
    @transaction.atomic
    def set_user_active(user, is_active):
        user.is_active = is_active
        user.save(update_fields=["is_active"])
        return user

    @staticmethod
    @transaction.atomic
    def set_user_verified(user, verified):
        user.is_verified = verified
        user.save(update_fields=["is_verified"])
        if verified:
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified_at"])
        return user


class StartupModerationRepository:
    """Data access for startup moderation."""

    @staticmethod
    def list_startups(status=None, verified=None, page=1, page_size=20):
        q = Q()
        if status:
            q &= Q(status=status)
        if verified is not None:
            q &= Q(is_verified=verified)

        offset = (page - 1) * page_size
        return (
            Startup.objects.filter(q)
            .order_by("-created_at")
            .select_related("owner")[offset:offset + page_size]
        )

    @staticmethod
    def get_startup_detail(startup_id):
        return Startup.objects.filter(id=startup_id).select_related("owner").first()

    @staticmethod
    @transaction.atomic
    def update_startup_status(startup, status):
        startup.status = status
        startup.save(update_fields=["status"])
        return startup

    @staticmethod
    @transaction.atomic
    def set_startup_verified(startup, verified):
        startup.is_verified = verified
        startup.save(update_fields=["is_verified"])
        if verified:
            from django.utils import timezone
            startup.verified_at = timezone.now()
            startup.save(update_fields=["verified_at"])
        return startup


class InvestmentOversightRepository:
    """Data access for investment oversight."""

    @staticmethod
    def list_opportunities(status=None, page=1, page_size=20):
        q = Q()
        if status:
            q &= Q(status=status)

        offset = (page - 1) * page_size
        return (
            InvestmentOpportunity.objects.filter(q)
            .order_by("-created_at")
            .select_related("investor", "startup")[offset:offset + page_size]
        )

    @staticmethod
    def pipeline_health():
        statuses = dict(InvestmentOpportunity.Status.choices)
        counts = {}
        for code, _ in statuses.items():
            counts[code] = InvestmentOpportunity.objects.filter(status=code).count()
        total = sum(counts.values()) or 1
        return {
            "total": total,
            "by_status": counts,
            "conversion_to_invested": round(
                (counts.get("invested", 0) / total) * 100, 1,
            ),
        }


class AuditLogRepository:
    """Data access for audit logs."""

    @staticmethod
    def create_log(actor, action_type, description="",
                   target_type="", target_id=None, target_repr="",
                   metadata=None, ip_address=None):
        return AuditLog.objects.create(
            actor=actor,
            action_type=action_type,
            description=description,
            target_type=target_type,
            target_id=target_id,
            target_repr=target_repr,
            metadata=metadata or {},
            ip_address=ip_address,
        )

    @staticmethod
    def search_logs(action_type=None, actor_id=None, target_type=None,
                    start_date=None, end_date=None, page=1, page_size=50):
        q = Q()
        if action_type:
            q &= Q(action_type=action_type)
        if actor_id:
            q &= Q(actor_id=actor_id)
        if target_type:
            q &= Q(target_type=target_type)
        if start_date:
            q &= Q(created_at__gte=start_date)
        if end_date:
            q &= Q(created_at__lte=end_date)

        offset = (page - 1) * page_size
        return (
            AuditLog.objects.filter(q)
            .select_related("actor")
            .order_by("-created_at")[offset:offset + page_size]
        )

    @staticmethod
    def get_log(log_id):
        return AuditLog.objects.filter(id=log_id).select_related("actor").first()

    @staticmethod
    def action_type_counts(days=30):
        cutoff = timezone.now() - timedelta(days=days)
        return list(
            AuditLog.objects.filter(created_at__gte=cutoff)
            .values("action_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )


class SupportTicketRepository:
    """Data access for support tickets."""

    @staticmethod
    def list_tickets(status=None, priority=None, category=None,
                     assigned_to=None, page=1, page_size=20):
        q = Q()
        if status:
            q &= Q(status=status)
        if priority:
            q &= Q(priority=priority)
        if category:
            q &= Q(category=category)
        if assigned_to:
            q &= Q(assigned_to_id=assigned_to)

        offset = (page - 1) * page_size
        return (
            SupportTicket.objects.filter(q)
            .select_related("user", "assigned_to")
            .order_by("-priority", "-updated_at")[offset:offset + page_size]
        )

    @staticmethod
    def get_ticket(ticket_id):
        return SupportTicket.objects.filter(id=ticket_id).select_related(
            "user", "assigned_to",
        ).first()

    @staticmethod
    @transaction.atomic
    def create_ticket(user, subject, description, category="other",
                      priority="medium"):
        return SupportTicket.objects.create(
            user=user,
            subject=subject,
            description=description,
            category=category,
            priority=priority,
        )

    @staticmethod
    @transaction.atomic
    def update_ticket(ticket, **kwargs):
        for key, value in kwargs.items():
            setattr(ticket, key, value)
        ticket.save()
        return ticket

    @staticmethod
    @transaction.atomic
    def add_message(ticket, sender, content, is_internal=False, attachments=None):
        return SupportMessage.objects.create(
            ticket=ticket,
            sender=sender,
            content=content,
            is_internal=is_internal,
            attachments=attachments or [],
        )

    @staticmethod
    def get_messages(ticket):
        return SupportMessage.objects.filter(ticket=ticket).select_related("sender").order_by("created_at")


class RevenueAnalyticsRepository:
    """Revenue aggregation from billing data."""

    @staticmethod
    def revenue_summary():
        from apps.billing.models import Invoice, SubscriptionPlan, UserSubscription

        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)

        active_subs = UserSubscription.objects.filter(status__in=["active", "trial"])
        plan_dist = list(
            active_subs.values("plan__tier", "plan__name")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        monthly_revenue = Invoice.objects.filter(
            status="paid",
            created_at__gte=month_start,
        ).aggregate(total=Sum("amount"))["total"] or 0

        last_month_revenue = Invoice.objects.filter(
            status="paid",
            created_at__gte=last_month_start,
            created_at__lt=month_start,
        ).aggregate(total=Sum("amount"))["total"] or 0

        total_revenue = Invoice.objects.filter(status="paid").aggregate(
            total=Sum("amount"),
        )["total"] or 0

        churned = UserSubscription.objects.filter(
            status="cancelled",
            updated_at__gte=month_start,
        ).count()

        trial_active = UserSubscription.objects.filter(status="trial").count()
        trial_converted = UserSubscription.objects.filter(
            status="active",
            created_at__gte=month_start,
            trial_end__isnull=False,
        ).count()

        return {
            "mrr": float(monthly_revenue),
            "last_month_revenue": float(last_month_revenue),
            "arr": float(monthly_revenue * 12),
            "total_revenue": float(total_revenue),
            "active_subscriptions": active_subs.count(),
            "plan_distribution": plan_dist,
            "churned_this_month": churned,
            "trial_active": trial_active,
            "trial_converted": trial_converted,
        }

    @staticmethod
    def plan_distribution():
        from apps.billing.models import UserSubscription
        return list(
            UserSubscription.objects.filter(status__in=["active", "trial"])
            .values("plan__name", "plan__slug", "plan__tier")
            .annotate(count=Count("id"))
            .order_by("-count")
        )


class RiskMonitoringRepository:
    """Risk monitoring data aggregation."""

    @staticmethod
    def risk_indicators():
        from apps.chat.models import Message
        from apps.activity_feed.models import ActivityFeed

        now = timezone.now()
        day_ago = now - timedelta(days=1)

        excessive_messaging = list(
            Message.objects.filter(created_at__gte=day_ago)
            .values("sender__email", "sender_id")
            .annotate(msg_count=Count("id"))
            .filter(msg_count__gt=100)
            .order_by("-msg_count")[:10]
        )

        rapid_activity = list(
            ActivityFeed.objects.filter(created_at__gte=day_ago)
            .values("actor__email", "actor_id")
            .annotate(activity_count=Count("id"))
            .filter(activity_count__gt=50)
            .order_by("-activity_count")[:10]
        )

        recent_bans = User.objects.filter(
            is_active=False,
            updated_at__gte=day_ago,
        ).count()

        return {
            "excessive_messaging": excessive_messaging,
            "rapid_activity": rapid_activity,
            "recent_bans_24h": recent_bans,
        }


class DataRoomModerationRepository:
    """Data access for data room moderation."""

    @staticmethod
    def list_documents(flagged_only=False, page=1, page_size=20):
        from apps.data_room.models import DataRoomDocument
        q = Q()
        if flagged_only:
            q &= Q(metadata__flagged=True)

        offset = (page - 1) * page_size
        return (
            DataRoomDocument.objects.filter(q)
            .select_related("data_room__startup", "uploaded_by")
            .order_by("-created_at")[offset:offset + page_size]
        )

    @staticmethod
    def get_document_views(document_id):
        from apps.data_room.models import DocumentViewEvent
        return DocumentViewEvent.objects.filter(document_id=document_id).select_related(
            "investor",
        ).order_by("-viewed_at")[:50]
