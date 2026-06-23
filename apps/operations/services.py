from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.common.exceptions import ApplicationError
from apps.startups.models import Startup

from .models import AuditLog, SupportTicket
from .repositories import (
    AuditLogRepository,
    DashboardRepository,
    DataRoomModerationRepository,
    InvestmentOversightRepository,
    RevenueAnalyticsRepository,
    RiskMonitoringRepository,
    StartupModerationRepository,
    SupportTicketRepository,
    UserManagementRepository,
)

User = get_user_model()


class OperationsService:
    """Business logic for admin operations console."""

    # ═══════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def dashboard():
        return DashboardRepository.platform_summary()

    # ═══════════════════════════════════════════════════════════════
    #  USER MANAGEMENT
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def search_users(query="", role=None, status=None, page=1):
        return UserManagementRepository.search_users(query, role, status, page)

    @staticmethod
    def get_user(user_id):
        user = UserManagementRepository.get_user_detail(user_id)
        if not user:
            raise ApplicationError("User not found", "NOT_FOUND", 404)
        return user

    @staticmethod
    def suspend_user(admin, user_id, reason=""):
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ApplicationError("User not found", "NOT_FOUND", 404)
        if not user.is_active:
            raise ApplicationError("User is already suspended", "ALREADY_SUSPENDED", 400)

        UserManagementRepository.set_user_active(user, False)
        AuditLogRepository.create_log(
            actor=admin,
            action_type=AuditLog.ActionType.USER_SUSPEND,
            description=f"User {user.email} suspended. Reason: {reason}",
            target_type="User",
            target_id=user.id,
            target_repr=user.email,
            metadata={"reason": reason},
            ip_address=getattr(admin, "last_login_ip", None),
        )
        return user

    @staticmethod
    def restore_user(admin, user_id, reason=""):
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ApplicationError("User not found", "NOT_FOUND", 404)
        if user.is_active:
            raise ApplicationError("User is already active", "ALREADY_ACTIVE", 400)

        UserManagementRepository.set_user_active(user, True)
        AuditLogRepository.create_log(
            actor=admin,
            action_type=AuditLog.ActionType.USER_RESTORE,
            description=f"User {user.email} restored. Reason: {reason}",
            target_type="User",
            target_id=user.id,
            target_repr=user.email,
            metadata={"reason": reason},
            ip_address=getattr(admin, "last_login_ip", None),
        )
        return user

    @staticmethod
    def verify_user(admin, user_id, verified=True):
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise ApplicationError("User not found", "NOT_FOUND", 404)

        UserManagementRepository.set_user_verified(user, verified)
        AuditLogRepository.create_log(
            actor=admin,
            action_type=AuditLog.ActionType.VERIFICATION_CHANGE,
            description=f"User {user.email} verification set to {verified}",
            target_type="User",
            target_id=user.id,
            target_repr=user.email,
            metadata={"verified": verified},
        )
        return user

    # ═══════════════════════════════════════════════════════════════
    #  STARTUP MODERATION
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def list_startups(status=None, verified=None, page=1):
        return StartupModerationRepository.list_startups(status, verified, page)

    @staticmethod
    def get_startup(startup_id):
        startup = StartupModerationRepository.get_startup_detail(startup_id)
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)
        return startup

    @staticmethod
    def moderate_startup(admin, startup_id, action, reason=""):
        startup = Startup.objects.filter(id=startup_id).first()
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)

        action_type_map = {
            "approve": (Startup.Status.ACTIVE, AuditLog.ActionType.STARTUP_APPROVE),
            "reject": (Startup.Status.DRAFT, AuditLog.ActionType.STARTUP_REJECT),
            "archive": (Startup.Status.CLOSED, AuditLog.ActionType.STARTUP_ARCHIVE),
            "flag": (None, AuditLog.ActionType.STARTUP_FLAG),
        }

        if action not in action_type_map:
            raise ApplicationError("Invalid action", "INVALID_ACTION", 400)

        new_status, log_action = action_type_map[action]
        if action == "flag":
            startup.is_verified = False
            startup.save(update_fields=["is_verified"])
        elif new_status:
            StartupModerationRepository.update_startup_status(startup, new_status)

        AuditLogRepository.create_log(
            actor=admin,
            action_type=log_action,
            description=f"Startup '{startup.name}' {action}d. Reason: {reason}",
            target_type="Startup",
            target_id=startup.id,
            target_repr=startup.name,
            metadata={"action": action, "reason": reason},
        )
        return startup

    @staticmethod
    def verify_startup(admin, startup_id, verified=True):
        startup = Startup.objects.filter(id=startup_id).first()
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)

        StartupModerationRepository.set_startup_verified(startup, verified)
        AuditLogRepository.create_log(
            actor=admin,
            action_type=AuditLog.ActionType.STARTUP_APPROVE if verified else AuditLog.ActionType.STARTUP_REJECT,
            description=f"Startup '{startup.name}' verification set to {verified}",
            target_type="Startup",
            target_id=startup.id,
            target_repr=startup.name,
            metadata={"verified": verified},
        )
        return startup

    # ═══════════════════════════════════════════════════════════════
    #  INVESTMENT OVERSIGHT
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def list_opportunities(status=None, page=1):
        return InvestmentOversightRepository.list_opportunities(status, page)

    @staticmethod
    def pipeline_health():
        return InvestmentOversightRepository.pipeline_health()

    # ═══════════════════════════════════════════════════════════════
    #  DATA ROOM MODERATION
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def list_documents(flagged_only=False, page=1):
        return DataRoomModerationRepository.list_documents(flagged_only, page)

    @staticmethod
    def get_document_views(document_id):
        return DataRoomModerationRepository.get_document_views(document_id)

    # ═══════════════════════════════════════════════════════════════
    #  SUPPORT TICKETS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def list_tickets(status=None, priority=None, category=None,
                     assigned_to=None, page=1):
        return SupportTicketRepository.list_tickets(
            status, priority, category, assigned_to, page,
        )

    @staticmethod
    def get_ticket(ticket_id):
        ticket = SupportTicketRepository.get_ticket(ticket_id)
        if not ticket:
            raise ApplicationError("Ticket not found", "NOT_FOUND", 404)
        return ticket

    @staticmethod
    def create_ticket(user, subject, description, category="other", priority="medium"):
        return SupportTicketRepository.create_ticket(
            user, subject, description, category, priority,
        )

    @staticmethod
    def update_ticket(admin, ticket_id, **kwargs):
        ticket = SupportTicketRepository.get_ticket(ticket_id)
        if not ticket:
            raise ApplicationError("Ticket not found", "NOT_FOUND", 404)

        old_status = ticket.status
        ticket = SupportTicketRepository.update_ticket(ticket, **kwargs)

        if "status" in kwargs and kwargs["status"] != old_status:
            AuditLogRepository.create_log(
                actor=admin,
                action_type=AuditLog.ActionType.TICKET_ACTION,
                description=f"Ticket '{ticket.subject}' status: {old_status} → {kwargs['status']}",
                target_type="SupportTicket",
                target_id=ticket.id,
                target_repr=ticket.subject[:100],
                metadata={"old_status": old_status, "new_status": kwargs["status"]},
            )
        return ticket

    @staticmethod
    def add_message(admin, ticket_id, content, is_internal=False, attachments=None):
        ticket = SupportTicketRepository.get_ticket(ticket_id)
        if not ticket:
            raise ApplicationError("Ticket not found", "NOT_FOUND", 404)

        msg = SupportTicketRepository.add_message(
            ticket, admin, content, is_internal, attachments,
        )

        if not is_internal and ticket.status == SupportTicket.Status.WAITING_ON_USER:
            SupportTicketRepository.update_ticket(ticket, status=SupportTicket.Status.IN_PROGRESS)

        return msg

    @staticmethod
    def get_ticket_messages(ticket_id):
        ticket = SupportTicketRepository.get_ticket(ticket_id)
        if not ticket:
            raise ApplicationError("Ticket not found", "NOT_FOUND", 404)
        return SupportTicketRepository.get_messages(ticket)

    # ═══════════════════════════════════════════════════════════════
    #  AUDIT LOGS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def search_logs(action_type=None, actor_id=None, target_type=None,
                    start_date=None, end_date=None, page=1):
        return AuditLogRepository.search_logs(
            action_type, actor_id, target_type,
            start_date, end_date, page,
        )

    @staticmethod
    def get_log(log_id):
        log = AuditLogRepository.get_log(log_id)
        if not log:
            raise ApplicationError("Log entry not found", "NOT_FOUND", 404)
        return log

    # ═══════════════════════════════════════════════════════════════
    #  REVENUE ANALYTICS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def revenue():
        return RevenueAnalyticsRepository.revenue_summary()

    # ═══════════════════════════════════════════════════════════════
    #  RISK MONITORING
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def risk():
        return RiskMonitoringRepository.risk_indicators()
