import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.common.exceptions import ApplicationError
from apps.common.pagination import StandardPagination

from .serializers import (
    ConversationListSerializer,
    ConversationDetailSerializer,
    MessageSerializer,
    MessageCreateSerializer,
    CreateConversationSerializer,
    UnreadCountSerializer,
)
from .services import ChatService

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Chat"],
    summary="List or create conversations",
    methods=["GET"],
    description="List all conversations for the current user with unread counts",
)
@extend_schema(
    tags=["Chat"],
    summary="Start a new conversation with a matched user",
    methods=["POST"],
    request=CreateConversationSerializer,
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    if request.method == "GET":
        conversations = ChatService.list_conversations(request.user)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(conversations, request)
        serializer = ConversationListSerializer(
            page if page else conversations,
            many=True,
            context={"request": request},
        )
        if page is not None:
            return paginator.get_paginated_response(
                {"status": "success", "data": serializer.data},
            )
        return Response({"status": "success", "data": serializer.data})

    serializer = CreateConversationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    conversation = ChatService.start_conversation(
        current_user=request.user,
        other_user_id=serializer.validated_data["participant_id"],
    )
    result = ConversationDetailSerializer(
        conversation, context={"request": request},
    )
    return Response(
        {"status": "success", "data": result.data},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Chat"],
    summary="Get conversation details",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def conversation_detail(request, conversation_id):
    conversation = ChatService.get_conversation(request.user, conversation_id)
    if not conversation.participants.filter(user=request.user).exists():
        raise PermissionDenied("You are not a participant in this conversation")
    serializer = ConversationDetailSerializer(
        conversation, context={"request": request},
    )
    return Response({"status": "success", "data": serializer.data})


@extend_schema(
    tags=["Chat"],
    summary="List or send messages in a conversation",
    methods=["GET"],
    description="Get paginated messages for a conversation (newest first)",
    parameters=[
        OpenApiParameter("before", str, description="ISO datetime cursor for pagination"),
        OpenApiParameter("limit", int, description="Max messages (default 50, max 100)"),
    ],
)
@extend_schema(
    tags=["Chat"],
    summary="Send a message in a conversation",
    methods=["POST"],
    request=MessageCreateSerializer,
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversation_messages(request, conversation_id):
    if request.method == "GET":
        before = request.GET.get("before")
        limit = request.GET.get("limit", 50)
        try:
            limit = min(int(limit), 100)
        except (ValueError, TypeError):
            limit = 50

        messages = ChatService.get_conversation_messages(
            request.user, conversation_id,
            before=before, limit=limit,
        )
        serializer = MessageSerializer(messages, many=True)
        return Response({"status": "success", "data": serializer.data})

    serializer = MessageCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    message = ChatService.send_message(
        current_user=request.user,
        conversation_id=conversation_id,
        message_type=serializer.validated_data["message_type"],
        content=serializer.validated_data.get("content", ""),
        attachment=serializer.validated_data.get("attachment"),
        metadata=serializer.validated_data.get("metadata", {}),
    )
    result = MessageSerializer(message)
    return Response(
        {"status": "success", "data": result.data},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Chat"],
    summary="Mark all messages as read in a conversation",
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request, conversation_id):
    ChatService.mark_read(request.user, conversation_id)
    return Response(
        {"status": "success", "data": {"message": "Marked as read"}},
    )


@extend_schema(
    tags=["Chat"],
    summary="Get total unread message count",
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def unread_count(request):
    count = ChatService.unread_count(request.user)
    serializer = UnreadCountSerializer(data={"count": count})
    serializer.is_valid(raise_exception=True)
    return Response({"status": "success", "data": serializer.data})
