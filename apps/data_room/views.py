from django.db import transaction

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.common.permissions import IsEntrepreneur, IsInvestor

from .models import DataRoom, DocumentAccess
from .repositories import DataRoomRepository
from .serializers import (
    DataRoomCreateSerializer,
    DataRoomDetailSerializer,
    DataRoomListSerializer,
    DataRoomUpdateSerializer,
    DataRoomDocumentDetailSerializer,
    DocumentAccessSerializer,
    DocumentUploadSerializer,
    DocumentViewSerializer,
    DocumentViewAnalyticsSerializer,
)
from .services import DataRoomService


class DataRoomViewSet(ViewSet):
    """Startup-side data room management."""

    permission_classes = [IsAuthenticated, IsEntrepreneur]

    def list(self, request):
        startup = request.user.startup_profile
        rooms = DataRoomService.list_rooms(startup, request.user)
        serializer = DataRoomListSerializer(rooms, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = DataRoomCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        startup = request.user.startup_profile
        room = DataRoomService.create_room(startup, request.user, serializer.validated_data)
        result = DataRoomDetailSerializer(room)
        return Response(result.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        room = DataRoomService.get_room(pk, request.user)
        if room.startup.owner_id != request.user.id:
            raise PermissionDenied("You do not own this data room")
        serializer = DataRoomDetailSerializer(room)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        serializer = DataRoomUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        room = DataRoomService.update_room(pk, request.user, serializer.validated_data)
        result = DataRoomDetailSerializer(room)
        return Response(result.data)

    def destroy(self, request, pk=None):
        room = DataRoomService.get_room(pk, request.user)
        DataRoomService._validate_startup_owner(room.startup, request.user)
        DataRoomRepository.delete_room(room)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def upload(self, request, pk=None):
        document_serializer = DocumentUploadSerializer(data=request.data)
        document_serializer.is_valid(raise_exception=True)
        doc = DataRoomService.upload_document(
            pk, request.user,
            document_serializer.validated_data,
            request.FILES.get("file"),
        )
        result = DataRoomDocumentDetailSerializer(doc)
        return Response(result.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        startup = request.user.startup_profile
        analytics = DataRoomService.get_startup_analytics(startup, request.user)
        return Response(analytics)

    @action(detail=False, methods=["get"])
    def full_analytics(self, request):
        startup = request.user.startup_profile
        analytics = DataRoomService.get_data_room_analytics(startup, request.user)
        return Response(analytics)


class DataRoomDocumentViewSet(ViewSet):
    """Startup-side document management within a data room."""

    permission_classes = [IsAuthenticated, IsEntrepreneur]

    def list(self, request):
        room_id = request.query_params.get("room_id")
        if not room_id:
            startup = request.user.startup_profile
            docs = DataRoomRepository.get_room_documents(
                DataRoom.objects.filter(startup=startup).first(),
            )
        else:
            room = DataRoomService.get_room(room_id, request.user)
            DataRoomService._validate_startup_owner(room.startup, request.user)
            docs = DataRoomRepository.get_room_documents(room)
        serializer = DataRoomDocumentDetailSerializer(docs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        doc = DataRoomRepository.get_document(pk)
        if not doc:
            return Response(
                {"detail": "Document not found"}, status=status.HTTP_404_NOT_FOUND,
            )
        DataRoomService._validate_startup_owner(doc.data_room.startup, request.user)
        serializer = DataRoomDocumentDetailSerializer(doc)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        serializer = DocumentUploadSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        file_obj = request.FILES.get("file")
        if file_obj:
            doc = DataRoomService.upload_new_version(pk, request.user, serializer.validated_data, file_obj)
        else:
            doc = DataRoomService.update_document(pk, request.user, serializer.validated_data)
        result = DataRoomDocumentDetailSerializer(doc)
        return Response(result.data)

    def destroy(self, request, pk=None):
        DataRoomService.delete_document(pk, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def grant(self, request, pk=None):
        serializer = DocumentAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access, created = DataRoomService.grant_document_access(
            pk, request.user, serializer.validated_data["investor_id"],
        )
        if created:
            return Response(status=status.HTTP_201_CREATED)
        return Response({"detail": "Access already granted"})

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        serializer = DocumentAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DataRoomService.revoke_document_access(
            pk, request.user, serializer.validated_data["investor_id"],
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def views(self, request, pk=None):
        doc = DataRoomRepository.get_document(pk)
        if not doc:
            return Response(
                {"detail": "Document not found"}, status=status.HTTP_404_NOT_FOUND,
            )
        DataRoomService._validate_startup_owner(doc.data_room.startup, request.user)
        events = DataRoomRepository.get_view_events(doc)
        serializer = DocumentViewAnalyticsSerializer(events, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def access_list(self, request, pk=None):
        doc = DataRoomRepository.get_document(pk)
        if not doc:
            return Response(
                {"detail": "Document not found"}, status=status.HTTP_404_NOT_FOUND,
            )
        DataRoomService._validate_startup_owner(doc.data_room.startup, request.user)
        grants = DataRoomRepository.get_investors_with_access(doc)
        data = [
            {
                "id": g.id,
                "investor_id": g.investor_id,
                "investor_email": g.investor.email,
                "granted_at": g.granted_at,
                "granted_by": g.granted_by_id,
            }
            for g in grants
        ]
        return Response(data)


class InvestorDocumentViewSet(ViewSet):
    """Investor-side document browsing."""

    permission_classes = [IsAuthenticated, IsInvestor]

    def list(self, request):
        docs = DataRoomService.list_shared_documents(request.user)
        serializer = DataRoomDocumentDetailSerializer(docs, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        doc = DataRoomService.get_document_for_investor(pk, request.user)
        serializer = DataRoomDocumentDetailSerializer(doc)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def view(self, request, pk=None):
        serializer = DocumentViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DataRoomService.record_document_view(
            pk, request.user,
            serializer.validated_data.get("duration_seconds"),
        )
        return Response(status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def analytics(self, request):
        analytics = DataRoomService.get_investor_analytics(request.user)
        return Response(analytics)
