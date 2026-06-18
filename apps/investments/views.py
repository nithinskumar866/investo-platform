import logging

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from apps.common.permissions import IsInvestor, IsEntrepreneur
from apps.common.exceptions import ApplicationError

from .services import InvestmentService
from .serializers import (
    InvestmentOpportunityListSerializer,
    InvestmentOpportunityDetailSerializer,
    CreateInvestmentOpportunitySerializer,
    UpdateStageSerializer,
    ScheduleMeetingSerializer,
    SendTermSheetSerializer,
    MarkInvestedSerializer,
    RejectDealSerializer,
    WithdrawDealSerializer,
    InvestorAnalyticsSerializer,
    StartupAnalyticsSerializer,
    InvestmentActivitySerializer,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=["Investments - Investor"], summary="List investor's pipeline"),
    create=extend_schema(tags=["Investments - Investor"], summary="Create investment opportunity"),
    retrieve=extend_schema(tags=["Investments - Investor"], summary="Get opportunity detail"),
)
class InvestorPipelineViewSet(viewsets.GenericViewSet):
    """Investor-facing pipeline: manage deal flow from interest to investment."""

    permission_classes = [IsAuthenticated, IsInvestor]
    serializer_class = InvestmentOpportunityListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return InvestmentOpportunityDetailSerializer
        if self.action == "create":
            return CreateInvestmentOpportunitySerializer
        if self.action == "analytics":
            return InvestorAnalyticsSerializer
        if self.action == "move_stage":
            return UpdateStageSerializer
        if self.action == "schedule_meeting":
            return ScheduleMeetingSerializer
        if self.action == "send_term_sheet":
            return SendTermSheetSerializer
        if self.action == "mark_invested":
            return MarkInvestedSerializer
        if self.action == "reject":
            return RejectDealSerializer
        if self.action == "withdraw":
            return WithdrawDealSerializer
        return self.serializer_class

    def get_queryset(self):
        status = self.request.GET.get("status")
        return InvestmentService.list_investor_pipeline(
            self.request.user, status=status,
        )

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page else qs, many=True,
        )
        if page is not None:
            return self.get_paginated_response(
                {"status": "success", "data": serializer.data},
            )
        return Response({"status": "success", "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.create_opportunity(
            investor=request.user,
            startup_id=serializer.validated_data["startup_id"],
            data=serializer.validated_data,
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response(
            {"status": "success", "data": result.data},
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        opportunity = InvestmentService._get_validated_opportunity(
            kwargs.get("pk"), request.user, "investor",
        )
        serializer = self.get_serializer(opportunity)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(summary="Move opportunity to a different stage")
    @action(detail=True, methods=["post"])
    def move_stage(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.move_stage(
            pk, request.user,
            serializer.validated_data["status"],
            notes=serializer.validated_data.get("notes"),
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Schedule a meeting with the founder")
    @action(detail=True, methods=["post"])
    def schedule_meeting(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.schedule_meeting(
            pk, request.user, serializer.validated_data,
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Send a term sheet")
    @action(detail=True, methods=["post"])
    def send_term_sheet(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.send_term_sheet(
            pk, request.user, serializer.validated_data,
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Mark deal as invested (closed)")
    @action(detail=True, methods=["post"])
    def mark_invested(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.mark_invested(
            pk, request.user, serializer.validated_data,
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Reject this deal")
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.reject_deal(
            pk, request.user,
            reason=serializer.validated_data.get("reason"),
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Withdraw from this deal")
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.withdraw_deal(
            pk, request.user,
            reason=serializer.validated_data.get("reason"),
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Get investor pipeline analytics")
    @action(detail=False, methods=["get"])
    def analytics(self, request):
        data = InvestmentService.get_investor_dashboard(request.user)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response({"status": "success", "data": serializer.data})


@extend_schema_view(
    list=extend_schema(tags=["Investments - Entrepreneur"], summary="List incoming opportunities"),
    retrieve=extend_schema(tags=["Investments - Entrepreneur"], summary="Get opportunity detail"),
)
class StartupPipelineViewSet(viewsets.GenericViewSet):
    """Startup-facing pipeline: view incoming investor interest and manage negotiations."""

    permission_classes = [IsAuthenticated, IsEntrepreneur]
    serializer_class = InvestmentOpportunityListSerializer

    def get_serializer_class(self):
        if self.action == "retrieve":
            return InvestmentOpportunityDetailSerializer
        if self.action == "analytics":
            return StartupAnalyticsSerializer
        if self.action == "move_stage":
            return UpdateStageSerializer
        if self.action == "reject":
            return RejectDealSerializer
        return self.serializer_class

    def get_queryset(self):
        startup_id = self.request.GET.get("startup_id")
        if not startup_id:
            raise ApplicationError("startup_id query parameter is required", "MISSING_PARAM", 400)
        return InvestmentService.list_startup_pipeline(startup_id, self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(
            page if page else qs, many=True,
        )
        if page is not None:
            return self.get_paginated_response(
                {"status": "success", "data": serializer.data},
            )
        return Response({"status": "success", "data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        opportunity = InvestmentService._get_validated_opportunity(
            kwargs.get("pk"), request.user, "entrepreneur",
        )
        serializer = self.get_serializer(opportunity)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(summary="Update stage of an opportunity (entrepreneur-side)")
    @action(detail=True, methods=["post"])
    def move_stage(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.move_stage(
            pk, request.user,
            serializer.validated_data["status"],
            notes=serializer.validated_data.get("notes"),
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Reject an incoming offer")
    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        opportunity = InvestmentService.reject_deal(
            pk, request.user,
            reason=serializer.validated_data.get("reason"),
        )
        result = InvestmentOpportunityDetailSerializer(opportunity)
        return Response({"status": "success", "data": result.data})

    @extend_schema(summary="Get startup investment analytics")
    @action(detail=False, methods=["get"])
    def analytics(self, request):
        startup_id = request.GET.get("startup_id")
        if not startup_id:
            raise ApplicationError("startup_id parameter required", "MISSING_PARAM", 400)
        from apps.startups.repositories import StartupRepository
        startup = StartupRepository.get_by_id(startup_id)
        if not startup:
            raise ApplicationError("Startup not found", "NOT_FOUND", 404)
        data = InvestmentService.get_startup_dashboard(startup, request.user)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response({"status": "success", "data": serializer.data})
