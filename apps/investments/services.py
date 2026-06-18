import logging

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import ApplicationError

from .models import InvestmentOpportunity
from .repositories import InvestmentRepository

logger = logging.getLogger(__name__)


class InvestmentService:
    """Business logic for the deal flow pipeline."""

    @staticmethod
    def _get_validated_opportunity(opportunity_id, user, role):
        opportunity = InvestmentRepository.get_opportunity(opportunity_id)
        if not opportunity:
            raise ApplicationError("Opportunity not found", "NOT_FOUND", 404)

        if role == "investor" and opportunity.investor_id != user.id:
            raise ApplicationError("Not your opportunity", "FORBIDDEN", 403)
        if role == "entrepreneur" and opportunity.startup.owner_id != user.id:
            raise ApplicationError("Not your startup's opportunity", "FORBIDDEN", 403)

        return opportunity

    @staticmethod
    def _transition_allowed(current, next_status) -> bool:
        flow = {
            InvestmentOpportunity.Status.INTERESTED: [
                InvestmentOpportunity.Status.MEETING_SCHEDULED,
                InvestmentOpportunity.Status.REJECTED,
                InvestmentOpportunity.Status.WITHDRAWN,
            ],
            InvestmentOpportunity.Status.MEETING_SCHEDULED: [
                InvestmentOpportunity.Status.DUE_DILIGENCE,
                InvestmentOpportunity.Status.REJECTED,
                InvestmentOpportunity.Status.WITHDRAWN,
            ],
            InvestmentOpportunity.Status.DUE_DILIGENCE: [
                InvestmentOpportunity.Status.NEGOTIATING,
                InvestmentOpportunity.Status.REJECTED,
                InvestmentOpportunity.Status.WITHDRAWN,
            ],
            InvestmentOpportunity.Status.NEGOTIATING: [
                InvestmentOpportunity.Status.TERM_SHEET_SENT,
                InvestmentOpportunity.Status.REJECTED,
                InvestmentOpportunity.Status.WITHDRAWN,
            ],
            InvestmentOpportunity.Status.TERM_SHEET_SENT: [
                InvestmentOpportunity.Status.INVESTED,
                InvestmentOpportunity.Status.NEGOTIATING,
                InvestmentOpportunity.Status.REJECTED,
                InvestmentOpportunity.Status.WITHDRAWN,
            ],
            InvestmentOpportunity.Status.INVESTED: [],
            InvestmentOpportunity.Status.REJECTED: [],
            InvestmentOpportunity.Status.WITHDRAWN: [],
        }
        return next_status in flow.get(current, [])

    # ── Pipeline operations ──────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_opportunity(investor, startup_id, data):
        from apps.startups.repositories import StartupRepository

        startup = StartupRepository.get_by_id(startup_id)
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)
        if not startup.is_visible:
            raise ApplicationError("Startup is not available", "UNAVAILABLE", 400)

        existing = InvestmentOpportunity.objects.filter(
            investor=investor, startup=startup,
        ).first()
        if existing:
            raise ApplicationError(
                "Opportunity already exists for this startup",
                "DUPLICATE", 400,
            )

        opportunity = InvestmentRepository.create_opportunity(startup, investor, data)

        InvestmentRepository.record_activity(
            opportunity, investor, "created",
            {"amount_requested": str(data.get("amount_requested", "")),
             "equity_requested": str(data.get("equity_requested", ""))},
        )

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=startup.owner,
            notification_type="deal_created",
            title="Investment Interest Received",
            message=f"{investor.email} is interested in investing in {startup.name}",
            actor=investor,
            data={
                "opportunity_id": opportunity.id,
                "startup_id": startup.id,
                "amount_requested": str(data.get("amount_requested", "")),
            },
        )

        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=investor,
            activity_type="investment_started",
            title=f"{investor.email} started investment in {startup.name}",
            startup=startup,
            investor=investor,
            target_object_id=opportunity.id,
            target_object_type="investment_opportunity",
            metadata={"amount_requested": str(data.get("amount_requested", ""))},
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=investor.id,
            event_type="investment_stage_changed",
            payload={"opportunity_id": opportunity.id, "old_status": None, "new_status": opportunity.status, "updated_by": investor.email, "timestamp": opportunity.created_at.isoformat()},
        )
        RealtimeService.broadcast_to_user(
            user_id=startup.owner_id,
            event_type="investment_stage_changed",
            payload={"opportunity_id": opportunity.id, "old_status": None, "new_status": opportunity.status, "updated_by": investor.email, "timestamp": opportunity.created_at.isoformat()},
        )

        logger.info(
            f"Investment opportunity created: {investor.email} → {startup.name}",
        )
        return opportunity

    @staticmethod
    @transaction.atomic
    def move_stage(opportunity_id, user, new_status, notes=None):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, user.role,
        )

        if not InvestmentService._transition_allowed(opportunity.status, new_status):
            raise ApplicationError(
                f"Cannot move from {opportunity.status} to {new_status}",
                "INVALID_TRANSITION", 400,
            )

        old_status = opportunity.status
        opportunity.status = new_status
        if notes:
            opportunity.notes = notes
        opportunity.save()

        InvestmentRepository.record_activity(
            opportunity, user, f"stage_changed:{old_status}→{new_status}",
            {"old_status": old_status, "new_status": new_status, "notes": notes},
        )

        logger.info(
            f"Opportunity {opportunity.id}: {old_status} → {new_status} by {user.email}",
        )

        from apps.notifications.services import NotificationService
        if user.role == "investor":
            NotificationService.notify(
                recipient=opportunity.startup.owner,
                notification_type="deal_stage_changed",
                title="Deal Stage Updated",
                message=f"Your deal with {user.email} moved from {old_status} to {new_status}",
                actor=user,
                data={
                    "opportunity_id": opportunity.id,
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )
        else:
            NotificationService.notify(
                recipient=opportunity.investor,
                notification_type="deal_stage_changed",
                title="Deal Stage Updated",
                message=f"Deal with {opportunity.startup.name} moved from {old_status} to {new_status}",
                actor=user,
                data={
                    "opportunity_id": opportunity.id,
                    "old_status": old_status,
                    "new_status": new_status,
                },
            )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=opportunity.investor_id,
            event_type="investment_stage_changed",
            payload={"opportunity_id": opportunity.id, "old_status": old_status, "new_status": new_status, "updated_by": user.email, "timestamp": timezone.now().isoformat()},
        )
        RealtimeService.broadcast_to_user(
            user_id=opportunity.startup.owner_id,
            event_type="investment_stage_changed",
            payload={"opportunity_id": opportunity.id, "old_status": old_status, "new_status": new_status, "updated_by": user.email, "timestamp": timezone.now().isoformat()},
        )

        return opportunity

    @staticmethod
    @transaction.atomic
    def schedule_meeting(opportunity_id, user, meeting_data):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, user.role,
        )

        if opportunity.status != InvestmentOpportunity.Status.INTERESTED:
            raise ApplicationError(
                "Can only schedule meetings on 'interested' opportunities",
                "INVALID_STATE", 400,
            )

        opportunity.status = InvestmentOpportunity.Status.MEETING_SCHEDULED
        opportunity.save()

        InvestmentRepository.record_activity(
            opportunity, user, "meeting_scheduled", meeting_data,
        )
        return opportunity

    @staticmethod
    @transaction.atomic
    def send_term_sheet(opportunity_id, user, term_data):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, "investor",
        )

        if opportunity.status != InvestmentOpportunity.Status.NEGOTIATING:
            raise ApplicationError(
                "Term sheet can only be sent during negotiation",
                "INVALID_STATE", 400,
            )

        opportunity.status = InvestmentOpportunity.Status.TERM_SHEET_SENT
        if "amount_offered" in term_data:
            opportunity.amount_offered = term_data["amount_offered"]
        if "equity_offered" in term_data:
            opportunity.equity_offered = term_data["equity_offered"]
        if "valuation" in term_data:
            opportunity.proposed_valuation = term_data["valuation"]
        if "term_sheet_url" in term_data:
            opportunity.term_sheet_url = term_data["term_sheet_url"]
        opportunity.save()

        InvestmentRepository.record_activity(
            opportunity, user, "term_sheet_sent", term_data,
        )

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=opportunity.startup.owner,
            notification_type="term_sheet_sent",
            title="Term Sheet Received",
            message=f"{user.email} has sent a term sheet for {opportunity.startup.name}",
            actor=user,
            data={
                "opportunity_id": opportunity.id,
                "amount_offered": str(term_data.get("amount_offered", "")),
                "equity_offered": str(term_data.get("equity_offered", "")),
            },
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=opportunity.investor_id,
            event_type="investment_term_sheet_sent",
            payload={"opportunity_id": opportunity.id, "investor_name": user.email, "amount_offered": str(term_data.get("amount_offered", "")), "equity_offered": str(term_data.get("equity_offered", "")), "timestamp": timezone.now().isoformat()},
        )
        RealtimeService.broadcast_to_user(
            user_id=opportunity.startup.owner_id,
            event_type="investment_term_sheet_sent",
            payload={"opportunity_id": opportunity.id, "investor_name": user.email, "amount_offered": str(term_data.get("amount_offered", "")), "equity_offered": str(term_data.get("equity_offered", "")), "timestamp": timezone.now().isoformat()},
        )

        return opportunity

    @staticmethod
    @transaction.atomic
    def mark_invested(opportunity_id, user, deal_data):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, "investor",
        )

        if opportunity.status != InvestmentOpportunity.Status.TERM_SHEET_SENT:
            raise ApplicationError(
                "Deal must be at 'term sheet sent' stage to mark invested",
                "INVALID_STATE", 400,
            )

        opportunity.status = InvestmentOpportunity.Status.INVESTED
        if "amount_offered" in deal_data:
            opportunity.amount_offered = deal_data["amount_offered"]
        if "equity_offered" in deal_data:
            opportunity.equity_offered = deal_data["equity_offered"]
        if "valuation" in deal_data:
            opportunity.valuation = deal_data["valuation"]
        opportunity.save()

        startup = opportunity.startup
        if startup.status != "funded":
            startup.status = "funded"
            startup.save(update_fields=["status"])

        InvestmentRepository.record_activity(
            opportunity, user, "invested", deal_data,
        )

        from apps.notifications.services import NotificationService
        NotificationService.notify(
            recipient=startup.owner,
            notification_type="investment_closed",
            title="Investment Closed!",
            message=f"{opportunity.investor.email} has invested in {startup.name}",
            actor=user,
            data={
                "opportunity_id": opportunity.id,
                "amount_offered": str(deal_data.get("amount_offered", "")),
                "equity_offered": str(deal_data.get("equity_offered", "")),
                "startup_id": startup.id,
            },
        )

        from apps.activity_feed.services import ActivityFeedService
        ActivityFeedService.publish_activity(
            actor=user,
            activity_type="investment_closed",
            title=f"{opportunity.investor.email} invested in {startup.name}!",
            startup=startup,
            investor=opportunity.investor,
            target_object_id=opportunity.id,
            target_object_type="investment_opportunity",
            metadata={
                "amount_offered": str(deal_data.get("amount_offered", "")),
                "equity_offered": str(deal_data.get("equity_offered", "")),
            },
        )
        ActivityFeedService.publish_activity(
            actor=startup.owner,
            activity_type="startup_funded",
            title=f"{startup.name} is now funded!",
            startup=startup,
            target_object_id=startup.id,
            target_object_type="startup",
            metadata={
                "investor": opportunity.investor.email,
                "amount": str(deal_data.get("amount_offered", "")),
            },
        )

        from apps.realtime.services import RealtimeService
        RealtimeService.broadcast_to_user(
            user_id=opportunity.investor_id,
            event_type="investment_closed",
            payload={"opportunity_id": opportunity.id, "startup_name": startup.name, "investor_name": opportunity.investor.email, "amount": str(deal_data.get("amount_offered", "")), "timestamp": timezone.now().isoformat()},
        )
        RealtimeService.broadcast_to_user(
            user_id=opportunity.startup.owner_id,
            event_type="investment_closed",
            payload={"opportunity_id": opportunity.id, "startup_name": startup.name, "investor_name": opportunity.investor.email, "amount": str(deal_data.get("amount_offered", "")), "timestamp": timezone.now().isoformat()},
        )

        logger.info(
            f"Deal closed: {opportunity.investor.email} invested in "
            f"{startup.name}",
        )
        return opportunity

    @staticmethod
    @transaction.atomic
    def reject_deal(opportunity_id, user, reason=None):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, user.role,
        )

        if opportunity.status in [
            InvestmentOpportunity.Status.INVESTED,
            InvestmentOpportunity.Status.REJECTED,
            InvestmentOpportunity.Status.WITHDRAWN,
        ]:
            raise ApplicationError("Deal is already closed", "ALREADY_CLOSED", 400)

        opportunity.status = InvestmentOpportunity.Status.REJECTED
        if reason:
            opportunity.notes = reason
        opportunity.save()

        InvestmentRepository.record_activity(
            opportunity, user, "rejected", {"reason": reason},
        )
        return opportunity

    @staticmethod
    @transaction.atomic
    def withdraw_deal(opportunity_id, user, reason=None):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, user.role,
        )

        if opportunity.status in [
            InvestmentOpportunity.Status.INVESTED,
            InvestmentOpportunity.Status.REJECTED,
            InvestmentOpportunity.Status.WITHDRAWN,
        ]:
            raise ApplicationError("Deal is already closed", "ALREADY_CLOSED", 400)

        opportunity.status = InvestmentOpportunity.Status.WITHDRAWN
        if reason:
            opportunity.notes = reason
        opportunity.save()

        InvestmentRepository.record_activity(
            opportunity, user, "withdrawn", {"reason": reason},
        )
        return opportunity

    # ── Dashboard ─────────────────────────────────────────────────

    @staticmethod
    def get_investor_dashboard(investor):
        return InvestmentRepository.get_investor_analytics(investor)

    @staticmethod
    def get_startup_dashboard(startup, user):
        if startup.owner_id != user.id:
            raise ApplicationError("Not your startup", "FORBIDDEN", 403)
        return InvestmentRepository.get_startup_analytics(startup)

    @staticmethod
    def list_investor_pipeline(investor, status=None):
        return InvestmentRepository.get_pipeline_for_investor(investor, status=status)

    @staticmethod
    def list_startup_pipeline(startup_id, user):
        from apps.startups.repositories import StartupRepository
        startup = StartupRepository.get_by_id(startup_id)
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)
        if startup.owner_id != user.id:
            raise ApplicationError("Not your startup", "FORBIDDEN", 403)
        return InvestmentRepository.get_pipeline_for_startup(startup)

    @staticmethod
    def get_activity_log(opportunity_id, user):
        opportunity = InvestmentService._get_validated_opportunity(
            opportunity_id, user, user.role,
        )
        return InvestmentRepository.get_activity_log(opportunity)
