import logging

from django.db import models

from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Startup
from .serializers import (
    StartupListSerializer, StartupDetailSerializer,
    StartupCreateSerializer, StartupUpdateSerializer,
)
from .filters import StartupFilter
from .permissions import CanCreateStartup, CanManageStartup
from .services import StartupService
from apps.common.permissions import IsAdmin
from apps.matching.services import MatchingService

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(tags=["Startups"], summary="List startups with filtering and search"),
    retrieve=extend_schema(tags=["Startups"], summary="Get startup details"),
    create=extend_schema(tags=["Startups"], summary="Create a new startup"),
    update=extend_schema(tags=["Startups"], summary="Full update a startup"),
    partial_update=extend_schema(tags=["Startups"], summary="Partial update a startup"),
    destroy=extend_schema(tags=["Startups"], summary="Delete a startup"),
)
class StartupViewSet(viewsets.ModelViewSet):
    filterset_class = StartupFilter
    search_fields = ["name", "tagline", "description", "location"]
    ordering_fields = [
        "created_at", "updated_at", "name", "funding_goal",
        "equity_offered", "view_count", "team_size",
    ]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "list":
            return StartupListSerializer
        if self.action in ("create", "update", "partial_update"):
            return StartupCreateSerializer
        return StartupDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), CanCreateStartup()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), CanManageStartup()]
        if self.action in ("verify", "statistics", "admin_list"):
            return [IsAuthenticated(), IsAdmin()]
        return [AllowAny()]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Startup.objects.filter(is_visible=True, status__in=["active", "funded"])
        queryset = StartupService.get_queryset(user)

        if self.action == "list":
            queryset = queryset.select_related("owner").only(
                "id", "name", "tagline", "industry", "stage",
                "funding_goal", "equity_offered", "location",
                "logo", "team_size", "is_verified", "status",
                "view_count", "bookmark_count", "created_at",
                "owner__first_name", "owner__last_name", "owner__email",
            )

        if self.action == "retrieve":
            queryset = queryset.select_related("owner", "metrics").prefetch_related(
                "team_members", "social_links", "documents", "funding_rounds",
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        StartupService.increment_view_count(instance)
        serializer = self.get_serializer(instance)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(tags=["Startups"], summary="Get startup statistics (admin)")
    @action(detail=False, methods=["get"])
    def statistics(self, request):
        data = StartupService.get_statistics()
        return Response({"status": "success", "data": data})

    @extend_schema(tags=["Startups"], summary="Verify a startup (admin)")
    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        startup = self.get_object()
        startup.is_verified = True
        startup.save(update_fields=["is_verified"])
        logger.info(f"Startup verified: {startup.name}")
        return Response({"status": "success", "data": {"message": "Startup verified"}})

    @extend_schema(tags=["Startups"], summary="List recommended investors for this startup")
    @action(detail=True, methods=["get"])
    def recommended_investors(self, request, pk=None):
        startup = self.get_object()
        investors = MatchingService.get_recommended_investors(startup)
        return Response({"status": "success", "data": investors})

    @extend_schema(tags=["Startups"], summary="Submit startup for review (change status to active)")
    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        startup = self.get_object()
        if startup.owner != request.user:
            return Response(
                {"status": "error", "error": {"code": "FORBIDDEN", "message": "Not your startup"}},
                status=403,
            )
        if startup.status != "draft":
            return Response(
                {"status": "error", "error": {"code": "INVALID_STATUS", "message": "Only draft startups can be submitted"}},
                status=400,
            )
        startup.status = "active"
        startup.save(update_fields=["status"])
        logger.info(f"Startup submitted: {startup.name}")
        return Response({"status": "success", "data": {"message": "Startup submitted for review"}})

    @extend_schema(tags=["Startups"], summary="Bookmark or unbookmark a startup")
    @action(detail=True, methods=["post", "delete"])
    @permission_classes([IsAuthenticated])
    def bookmark(self, request, pk=None):
        startup = self.get_object()
        if request.method == "POST":
            Startup.objects.filter(pk=startup.pk).update(bookmark_count=models.F("bookmark_count") + 1)
            startup.refresh_from_db()
            logger.info(f"Startup bookmarked: {startup.name} by {request.user.email}")
            return Response({"status": "success", "data": {"bookmarked": True, "bookmark_count": startup.bookmark_count}})
        else:
            Startup.objects.filter(pk=startup.pk).update(bookmark_count=models.F("bookmark_count") - 1)
            startup.refresh_from_db()
            logger.info(f"Startup unbookmarked: {startup.name} by {request.user.email}")
            return Response({"status": "success", "data": {"bookmarked": False, "bookmark_count": startup.bookmark_count}})

    @extend_schema(tags=["Startups"], summary="Upload a document for this startup")
    @action(detail=True, methods=["post"], parser_classes=[])
    @permission_classes([IsAuthenticated, CanManageStartup])
    def upload_document(self, request, pk=None):
        from .models import StartupDocument
        from .serializers import StartupDocumentSerializer

        startup = self.get_object()
        serializer = StartupDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(startup=startup)
        logger.info(f"Document uploaded for startup: {startup.name}")
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["Startups"], summary="List documents for this startup")
    @action(detail=True, methods=["get"])
    def documents(self, request, pk=None):
        from .models import StartupDocument
        from .serializers import StartupDocumentSerializer

        startup = self.get_object()
        docs = startup.documents.all()
        serializer = StartupDocumentSerializer(docs, many=True)
        return Response({"status": "success", "data": serializer.data})

    @extend_schema(
        tags=["Startups"],
        summary="Delete a document from this startup",
        parameters=[
            {
                "name": "doc_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": "Document ID",
            }
        ],
    )
    @action(detail=True, methods=["delete"], url_path="documents/(?P<doc_id>[^/.]+)")
    @permission_classes([IsAuthenticated, CanManageStartup])
    def delete_document(self, request, pk=None, doc_id=None):
        from .models import StartupDocument

        startup = self.get_object()
        try:
            doc = startup.documents.get(pk=doc_id)
            doc.delete()
            logger.info(f"Document deleted for startup: {startup.name}")
            return Response({"status": "success", "data": {"message": "Document deleted"}})
        except StartupDocument.DoesNotExist:
            return Response(
                {"status": "error", "error": {"code": "NOT_FOUND", "message": "Document not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )
