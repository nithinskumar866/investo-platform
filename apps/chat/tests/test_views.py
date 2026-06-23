import pytest
from unittest.mock import patch

from django.urls import reverse

from conftest import get_data, assert_success_response, assert_error_response

from apps.accounts.models import User
from apps.chat.models import Conversation, Message
from apps.common.tests.factories import (
    UserFactory, FounderFactory, InvestorFactory,
    StartupFactory, MatchScoreFactory,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def founder():
    return FounderFactory()


@pytest.fixture
def investor():
    return InvestorFactory()


@pytest.fixture
def startup(founder):
    return StartupFactory(owner=founder)


@pytest.fixture
def match(investor, startup):
    return MatchScoreFactory(investor=investor, startup=startup)


@pytest.fixture
def conversation(founder, investor, match):
    from apps.chat.services import ChatService
    return ChatService.start_conversation(founder, investor.id)


LIST_URL = reverse("chat-conversation-list")
UNREAD_URL = reverse("chat-unread-count")


def detail_url(cid):
    return reverse("chat-conversation-detail", args=[cid])


def messages_url(cid):
    return reverse("chat-conversation-messages", args=[cid])


def read_url(cid):
    return reverse("chat-mark-read", args=[cid])


class TestListConversations:
    def test_returns_user_conversations(self, founder_client, conversation):
        response = founder_client.get(LIST_URL)
        assert_success_response(response)
        data = get_data(response)
        ids = [c["id"] for c in data["results"]]
        assert conversation.id in ids

    def test_returns_empty_list_for_no_conversations(self, founder_client):
        response = founder_client.get(LIST_URL)
        assert_success_response(response)
        data = get_data(response)
        assert len(data["results"]) == 0

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(LIST_URL)
        assert response.status_code == 401


class TestCreateConversation:
    def test_creates_conversation(self, founder_client, investor, match):
        response = founder_client.post(LIST_URL, {"participant_id": investor.id})
        assert_success_response(response, 201)
        data = get_data(response)
        assert data["is_active"] is True
        participant_ids = [p["id"] for p in data["participants"]]
        assert investor.id in participant_ids

    def test_created_conversation_has_correct_participants(
        self, founder_client, founder, investor, match,
    ):
        response = founder_client.post(LIST_URL, {"participant_id": investor.id})
        data = get_data(response)
        participant_ids = [p["id"] for p in data["participants"]]
        assert founder.id in participant_ids
        assert investor.id in participant_ids
        assert len(participant_ids) == 2

    def test_returns_existing_conversation(self, founder_client, founder, investor, match):
        from apps.chat.services import ChatService
        existing = ChatService.start_conversation(founder, investor.id)
        response = founder_client.post(LIST_URL, {"participant_id": investor.id})
        assert_success_response(response, 201)
        data = get_data(response)
        assert data["id"] == existing.id

    def test_unauthenticated_returns_401(self, api_client, investor):
        response = api_client.post(LIST_URL, {"participant_id": investor.id})
        assert response.status_code == 401


class TestConversationDetail:
    def test_returns_conversation(self, founder_client, conversation):
        response = founder_client.get(detail_url(conversation.id))
        assert_success_response(response)
        data = get_data(response)
        assert data["id"] == conversation.id

    def test_non_participant_cannot_access(self, investor_client, conversation):
        """An investor not in the conversation gets 403."""
        stranger = UserFactory()
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(stranger)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = client.get(detail_url(conversation.id))
        assert response.status_code == 403

    def test_unauthenticated_returns_401(self, api_client, conversation):
        response = api_client.get(detail_url(conversation.id))
        assert response.status_code == 401


class TestConversationMessages:
    def test_list_messages(self, founder_client, conversation):
        response = founder_client.get(messages_url(conversation.id))
        assert_success_response(response)

    def test_send_message(self, founder_client, conversation):
        response = founder_client.post(
            messages_url(conversation.id),
            {"message_type": "text", "content": "Hello!"},
        )
        assert_success_response(response, 201)
        data = get_data(response)
        assert data["content"] == "Hello!"

    def test_non_participant_cannot_send(self, conversation):
        stranger = UserFactory()
        from rest_framework.test import APIClient
        from rest_framework_simplejwt.tokens import RefreshToken
        client = APIClient()
        refresh = RefreshToken.for_user(stranger)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        response = client.post(
            messages_url(conversation.id),
            {"message_type": "text", "content": "Hi"},
        )
        assert response.status_code in (403, 404)

    def test_unauthenticated_cannot_list(self, api_client, conversation):
        response = api_client.get(messages_url(conversation.id))
        assert response.status_code == 401

    def test_unauthenticated_cannot_send(self, api_client, conversation):
        response = api_client.post(
            messages_url(conversation.id),
            {"message_type": "text", "content": "Hi"},
        )
        assert response.status_code == 401


class TestMarkRead:
    def test_mark_read(self, founder_client, conversation):
        response = founder_client.post(read_url(conversation.id))
        assert_success_response(response)

    def test_unauthenticated_returns_401(self, api_client, conversation):
        response = api_client.post(read_url(conversation.id))
        assert response.status_code == 401


class TestUnreadCount:
    def test_returns_unread_count(self, founder_client):
        response = founder_client.get(UNREAD_URL)
        assert_success_response(response)
        data = get_data(response)
        assert "count" in data

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(UNREAD_URL)
        assert response.status_code == 401
