from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from apps.common.exceptions import ApplicationError

from .serializers import (
    AuditLogFilterSerializer,
    AuditLogSerializer,
    StartupFilterSerializer,
    SupportMessageCreateSerializer,
    SupportMessageSerializer,
    SupportTicketCreateSerializer,
    SupportTicketDetailSerializer,
    SupportTicketListSerializer,
    SupportTicketUpdateSerializer,
    UserActionSerializer,
    UserSearchSerializer,
)
from .services import OperationsService


def admin_required(view_func):
    return permission_classes([IsAuthenticated, IsAdminUser])(view_func)


# ═══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def dashboard(request):
    data = OperationsService.dashboard()
    return Response(data)


# ═══════════════════════════════════════════════════════════════════
#  USER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def user_list(request):
    serializer = UserSearchSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    users = OperationsService.search_users(
        query=serializer.validated_data.get("query", ""),
        role=serializer.validated_data.get("role"),
        status=serializer.validated_data.get("status"),
        page=serializer.validated_data.get("page", 1),
    )
    return Response([
        {
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "role": u.role,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "date_joined": u.date_joined.isoformat() if hasattr(u, "date_joined") else None,
        }
        for u in users
    ])


@api_view(["GET"])
@admin_required
def user_detail(request, user_id):
    user = OperationsService.get_user(user_id)
    data = {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "phone": user.phone,
        "date_joined": user.date_joined.isoformat() if hasattr(user, "date_joined") else None,
        "has_entrepreneur_profile": hasattr(user, "entrepreneur_profile"),
        "has_investor_profile": hasattr(user, "investor_profile"),
        "subscription": {
            "plan": user.subscription.plan.name if hasattr(user, "subscription") and user.subscription and user.subscription.plan else None,
            "status": user.subscription.status if hasattr(user, "subscription") and user.subscription else None,
        } if hasattr(user, "subscription") else None,
    }
    return Response(data)


@api_view(["POST"])
@admin_required
def user_suspend(request, user_id):
    reason = request.data.get("reason", "")
    user = OperationsService.suspend_user(request.user, user_id, reason)
    return Response({"detail": f"User {user.email} suspended"})


@api_view(["POST"])
@admin_required
def user_restore(request, user_id):
    reason = request.data.get("reason", "")
    user = OperationsService.restore_user(request.user, user_id, reason)
    return Response({"detail": f"User {user.email} restored"})


@api_view(["POST"])
@admin_required
def user_verify(request, user_id):
    verified = request.data.get("verified", True)
    user = OperationsService.verify_user(request.user, user_id, verified)
    return Response({"detail": f"User {user.email} verified={verified}"})


# ═══════════════════════════════════════════════════════════════════
#  STARTUP MODERATION
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def startup_list(request):
    serializer = StartupFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    startups = OperationsService.list_startups(
        status=serializer.validated_data.get("status"),
        verified=serializer.validated_data.get("verified"),
        page=serializer.validated_data.get("page", 1),
    )
    return Response([
        {
            "id": s.id,
            "name": s.name,
            "industry": s.industry,
            "stage": s.stage,
            "status": s.status,
            "is_verified": s.is_verified,
            "is_visible": s.is_visible,
            "owner_email": s.owner.email,
            "created_at": s.created_at.isoformat(),
        }
        for s in startups
    ])


@api_view(["GET"])
@admin_required
def startup_detail(request, startup_id):
    startup = OperationsService.get_startup(startup_id)
    data = {
        "id": startup.id,
        "name": startup.name,
        "tagline": startup.tagline,
        "industry": startup.industry,
        "stage": startup.stage,
        "status": startup.status,
        "is_verified": startup.is_verified,
        "is_visible": startup.is_visible,
        "owner": {
            "id": startup.owner.id,
            "email": startup.owner.email,
            "name": f"{startup.owner.first_name} {startup.owner.last_name}".strip(),
            "is_verified": startup.owner.is_verified,
        },
        "funding_goal": float(startup.funding_goal) if startup.funding_goal else None,
        "valuation": float(startup.valuation) if startup.valuation else None,
        "team_size": startup.team_size,
        "view_count": startup.view_count,
        "created_at": startup.created_at.isoformat(),
    }
    return Response(data)


@api_view(["POST"])
@admin_required
def startup_moderate(request, startup_id):
    serializer = UserActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    startup = OperationsService.moderate_startup(
        request.user, startup_id,
        serializer.validated_data["action"],
        serializer.validated_data.get("reason", ""),
    )
    return Response({"detail": f"Startup '{startup.name}' {serializer.validated_data['action']}d"})


@api_view(["POST"])
@admin_required
def startup_verify(request, startup_id):
    verified = request.data.get("verified", True)
    startup = OperationsService.verify_startup(request.user, startup_id, verified)
    return Response({"detail": f"Startup '{startup.name}' verified={verified}"})


# ═══════════════════════════════════════════════════════════════════
#  INVESTMENT OVERSIGHT
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def investment_list(request):
    status_filter = request.query_params.get("status")
    page = int(request.query_params.get("page", 1))
    opportunities = OperationsService.list_opportunities(status_filter, page)
    return Response([
        {
            "id": o.id,
            "startup_name": o.startup.name if o.startup else "N/A",
            "investor_email": o.investor.email,
            "amount_requested": float(o.amount_requested) if o.amount_requested else None,
            "amount_offered": float(o.amount_offered) if o.amount_offered else None,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
        }
        for o in opportunities
    ])


@api_view(["GET"])
@admin_required
def pipeline_health(request):
    data = OperationsService.pipeline_health()
    return Response(data)


# ═══════════════════════════════════════════════════════════════════
#  SUPPORT TICKETS
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_list(request):
    if request.user.is_staff:
        status_filter = request.query_params.get("status")
        priority = request.query_params.get("priority")
        category = request.query_params.get("category")
        assigned_to = request.query_params.get("assigned_to")
        page = int(request.query_params.get("page", 1))
        tickets = OperationsService.list_tickets(
            status_filter, priority, category, assigned_to, page,
        )
    else:
        qstatus = request.query_params.get("status")
        page = int(request.query_params.get("page", 1))
        tickets = [
            t for t in OperationsService.list_tickets(status=qstatus, page=page)
            if t.user_id == request.user.id
        ]
    serializer = SupportTicketListSerializer(tickets, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_detail(request, ticket_id):
    ticket = OperationsService.get_ticket(ticket_id)
    if not request.user.is_staff and ticket.user_id != request.user.id:
        raise ApplicationError("Not found", "NOT_FOUND", 404)
    serializer = SupportTicketDetailSerializer(ticket)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ticket_create(request):
    serializer = SupportTicketCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ticket = OperationsService.create_ticket(
        request.user,
        serializer.validated_data["subject"],
        serializer.validated_data.get("description", ""),
        serializer.validated_data.get("category", "other"),
        serializer.validated_data.get("priority", "medium"),
    )
    out = SupportTicketDetailSerializer(ticket)
    return Response(out.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@admin_required
def ticket_update(request, ticket_id):
    serializer = SupportTicketUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    ticket = OperationsService.update_ticket(
        request.user, ticket_id, **serializer.validated_data,
    )
    out = SupportTicketDetailSerializer(ticket)
    return Response(out.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_messages(request, ticket_id):
    ticket = OperationsService.get_ticket(ticket_id)
    if not request.user.is_staff and ticket.user_id != request.user.id:
        raise ApplicationError("Not found", "NOT_FOUND", 404)

    messages = OperationsService.get_ticket_messages(ticket_id)
    if not request.user.is_staff:
        messages = [m for m in messages if not m.is_internal]
    serializer = SupportMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@admin_required
def ticket_send_message(request, ticket_id):
    serializer = SupportMessageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    msg = OperationsService.add_message(
        request.user, ticket_id,
        serializer.validated_data["content"],
        serializer.validated_data.get("is_internal", False),
        serializer.validated_data.get("attachments"),
    )
    out = SupportMessageSerializer(msg)
    return Response(out.data, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════
#  AUDIT LOGS
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def audit_log_list(request):
    serializer = AuditLogFilterSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    logs = OperationsService.search_logs(
        action_type=serializer.validated_data.get("action_type"),
        actor_id=serializer.validated_data.get("actor_id"),
        target_type=serializer.validated_data.get("target_type"),
        start_date=serializer.validated_data.get("start_date"),
        end_date=serializer.validated_data.get("end_date"),
        page=serializer.validated_data.get("page", 1),
    )
    out = AuditLogSerializer(logs, many=True)
    return Response(out.data)


@api_view(["GET"])
@admin_required
def audit_log_detail(request, log_id):
    log = OperationsService.get_log(log_id)
    serializer = AuditLogSerializer(log)
    return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════
#  REVENUE ANALYTICS
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def revenue(request):
    data = OperationsService.revenue()
    return Response(data)


# ═══════════════════════════════════════════════════════════════════
#  RISK MONITORING
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def risk(request):
    data = OperationsService.risk()
    return Response(data)


# ═══════════════════════════════════════════════════════════════════
#  DATA ROOM MODERATION
# ═══════════════════════════════════════════════════════════════════


@api_view(["GET"])
@admin_required
def document_list(request):
    flagged_only = request.query_params.get("flagged", "").lower() == "true"
    page = int(request.query_params.get("page", 1))
    docs = OperationsService.list_documents(flagged_only, page)
    return Response([
        {
            "id": d.id,
            "title": d.title,
            "document_type": d.document_type,
            "startup_name": d.data_room.startup.name if d.data_room and d.data_room.startup else "N/A",
            "uploaded_by_email": d.uploaded_by.email,
            "file_size": d.file_size,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ])


@api_view(["GET"])
@admin_required
def document_views(request, document_id):
    views = OperationsService.get_document_views(document_id)
    return Response([
        {
            "investor_email": v.investor.email,
            "viewed_at": v.viewed_at.isoformat(),
            "duration_seconds": v.duration_seconds,
        }
        for v in views
    ])
