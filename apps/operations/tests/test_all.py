import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.accounts.models import User
from apps.startups.models import Startup
from apps.operations.models import AuditLog, SupportTicket, SupportMessage
from apps.operations.services import OperationsService
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
    )


@pytest.fixture
def investor(db):
    return User.objects.create_user(
        email="investor@example.com", password="testpass123", role="investor",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com", password="testpass123", role="admin",
        is_staff=True, is_superuser=True,
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
        status=Startup.Status.ACTIVE,
        is_verified=True,
        is_visible=True,
    )


@pytest.fixture
def audit_log(db, admin_user):
    return AuditLog.objects.create(
        actor=admin_user,
        action_type=AuditLog.ActionType.ADMIN_ACTION,
        target_type="User",
        target_id=1,
        target_repr="test@example.com",
        description="Admin action test",
    )


@pytest.fixture
def ticket(db, user):
    return SupportTicket.objects.create(
        user=user,
        subject="Test Issue",
        description="Need help",
        category="technical",
        priority="medium",
        status=SupportTicket.Status.OPEN,
    )


# ── Model tests ──────────────────────────────────────────────────────────

class TestAuditLogModel:
    def test_create_audit_log(self, audit_log):
        assert audit_log.pk is not None
        assert audit_log.action_type == AuditLog.ActionType.ADMIN_ACTION
        assert str(audit_log).startswith("admin_action")

    def test_action_type_choices(self):
        assert AuditLog.ActionType.USER_BAN == "user_ban"
        assert AuditLog.ActionType.STARTUP_APPROVE == "startup_approve"


class TestSupportTicketModel:
    def test_create_ticket(self, ticket):
        assert ticket.pk is not None
        assert ticket.status == SupportTicket.Status.OPEN
        assert str(ticket) == "[Open] Test Issue"

    def test_lifecycle(self, ticket):
        ticket.status = SupportTicket.Status.IN_PROGRESS
        ticket.save()
        ticket.status = SupportTicket.Status.RESOLVED
        ticket.save()
        ticket.refresh_from_db()
        assert ticket.status == SupportTicket.Status.RESOLVED

    def test_priority_choices(self):
        assert SupportTicket.Priority.LOW == "low"
        assert SupportTicket.Priority.CRITICAL == "critical"


class TestSupportMessageModel:
    def test_create_message(self, ticket, user):
        msg = SupportMessage.objects.create(
            ticket=ticket,
            sender=user,
            content="This is a message",
            is_internal=False,
        )
        assert msg.pk is not None
        assert msg.content == "This is a message"


# ── Service tests ────────────────────────────────────────────────────────

class TestOperationsService:
    def test_dashboard(self):
        data = OperationsService.dashboard()
        assert isinstance(data, dict)

    def test_search_users(self, user):
        results = OperationsService.search_users(query="user@")
        assert len(results) >= 1

    def test_search_users_by_role(self, user):
        results = OperationsService.search_users(role="entrepreneur")
        assert len(results) >= 1

    def test_get_user(self, user):
        result = OperationsService.get_user(user.id)
        assert result.email == user.email

    def test_get_user_not_found(self):
        with pytest.raises(ApplicationError, match="not found"):
            OperationsService.get_user(9999)

    def test_suspend_user(self, admin_user, user):
        result = OperationsService.suspend_user(admin_user, user.id, "Test suspend")
        assert result.is_active is False

    def test_suspend_already_suspended(self, admin_user, user):
        user.is_active = False
        user.save()
        with pytest.raises(ApplicationError, match="already suspended"):
            OperationsService.suspend_user(admin_user, user.id, "")

    def test_restore_user(self, admin_user, user):
        user.is_active = False
        user.save()
        result = OperationsService.restore_user(admin_user, user.id, "Test restore")
        assert result.is_active is True

    def test_moderate_startup(self, admin_user, startup):
        result = OperationsService.moderate_startup(
            admin_user, startup.id, "approve", "Approved",
        )
        assert result.status == Startup.Status.ACTIVE

    def test_moderate_startup_invalid_action(self, admin_user, startup):
        with pytest.raises(ApplicationError, match="Invalid action"):
            OperationsService.moderate_startup(admin_user, startup.id, "invalid", "")

    def test_moderate_startup_flag(self, admin_user, startup):
        result = OperationsService.moderate_startup(
            admin_user, startup.id, "flag", "Flagged",
        )
        assert result.is_verified is False

    def test_startup_not_found(self, admin_user):
        with pytest.raises(ApplicationError, match="not found"):
            OperationsService.moderate_startup(admin_user, 9999, "approve", "")

    def test_list_startups(self, startup):
        results = OperationsService.list_startups()
        assert startup in results

    def test_get_startup(self, startup):
        result = OperationsService.get_startup(startup.id)
        assert result.name == startup.name

    def test_create_ticket(self, user):
        ticket = OperationsService.create_ticket(
            user, "New Issue", "Description", "technical", "high",
        )
        assert ticket.subject == "New Issue"
        assert ticket.priority == "high"

    def test_update_ticket(self, admin_user, ticket):
        updated = OperationsService.update_ticket(
            admin_user, ticket.id, status="resolved",
        )
        assert updated.status == SupportTicket.Status.RESOLVED

    def test_add_message(self, admin_user, ticket):
        msg = OperationsService.add_message(
            admin_user, ticket.id, "Admin response", is_internal=False,
        )
        assert msg.content == "Admin response"

    def test_search_logs(self, audit_log):
        logs = OperationsService.search_logs()
        assert audit_log in logs

    def test_get_log(self, audit_log):
        log = OperationsService.get_log(audit_log.id)
        assert log.id == audit_log.id


# ── View tests ──────────────────────────────────────────────────────────

class TestOperationsViews:
    def test_dashboard(self, admin_client):
        resp = admin_client.get("/api/v1/ops/dashboard/")
        assert resp.status_code == 200

    def test_dashboard_forbidden(self, authenticated_client):
        resp = authenticated_client.get("/api/v1/ops/dashboard/")
        assert resp.status_code == 403

    def test_user_list(self, admin_client, user):
        resp = admin_client.get("/api/v1/ops/users/")
        assert resp.status_code == 200

    def test_user_detail(self, admin_client, user):
        resp = admin_client.get(f"/api/v1/ops/users/{user.id}/")
        assert resp.status_code == 200

    def test_user_suspend(self, admin_client, user):
        resp = admin_client.post(
            f"/api/v1/ops/users/{user.id}/suspend/",
            {"reason": "Test"},
            format="json",
        )
        assert resp.status_code == 200

    def test_user_restore(self, admin_client, user):
        user.is_active = False
        user.save()
        resp = admin_client.post(
            f"/api/v1/ops/users/{user.id}/restore/",
            {"reason": "Restored"},
            format="json",
        )
        assert resp.status_code == 200

    def test_startup_list(self, admin_client, startup):
        resp = admin_client.get("/api/v1/ops/startups/")
        assert resp.status_code == 200

    def test_startup_moderate(self, admin_client, startup):
        resp = admin_client.post(
            f"/api/v1/ops/startups/{startup.id}/moderate/",
            {"action": "approve"},
            format="json",
        )
        assert resp.status_code == 200

    def test_startup_verify(self, admin_client, startup):
        resp = admin_client.post(
            f"/api/v1/ops/startups/{startup.id}/verify/",
            {"verified": True},
            format="json",
        )
        assert resp.status_code == 200

    def test_ticket_list(self, admin_client, ticket):
        resp = admin_client.get("/api/v1/ops/tickets/")
        assert resp.status_code == 200

    def test_ticket_list_non_admin(self, authenticated_client, ticket):
        resp = authenticated_client.get("/api/v1/ops/tickets/")
        assert resp.status_code == 200

    def test_ticket_create(self, admin_client):
        resp = admin_client.post(
            "/api/v1/ops/tickets/create/",
            {"subject": "Issue", "description": "Desc", "category": "technical"},
            format="json",
        )
        assert resp.status_code == 201

    def test_ticket_detail(self, admin_client, ticket):
        resp = admin_client.get(f"/api/v1/ops/tickets/{ticket.id}/")
        assert resp.status_code == 200

    def test_ticket_update(self, admin_client, ticket):
        resp = admin_client.patch(
            f"/api/v1/ops/tickets/{ticket.id}/update/",
            {"status": "resolved"},
            format="json",
        )
        assert resp.status_code == 200

    def test_audit_log_list(self, admin_client, audit_log):
        resp = admin_client.get("/api/v1/ops/audit/")
        assert resp.status_code == 200

    def test_audit_log_detail(self, admin_client, audit_log):
        resp = admin_client.get(f"/api/v1/ops/audit/{audit_log.id}/")
        assert resp.status_code == 200

    def test_revenue(self, admin_client):
        resp = admin_client.get("/api/v1/ops/revenue/")
        assert resp.status_code == 200

    def test_risk(self, admin_client):
        resp = admin_client.get("/api/v1/ops/risk/")
        assert resp.status_code == 200

    def test_document_list(self, admin_client):
        resp = admin_client.get("/api/v1/ops/documents/")
        assert resp.status_code == 200
