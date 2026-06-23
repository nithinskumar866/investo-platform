import pytest
from unittest.mock import patch

from django.db import IntegrityError

from apps.accounts.models import User
from apps.chat.models import Conversation, ConversationParticipant, Message, MessageReadStatus
from apps.chat.services import ChatService
from apps.common.exceptions import ApplicationError
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


class TestStartConversation:
    def test_creates_conversation_with_two_participants(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        assert conversation is not None
        assert conversation.participants.count() == 2
        assert conversation.created_by == founder

    def test_returns_existing_conversation(self, founder, investor, match):
        c1 = ChatService.start_conversation(founder, investor.id)
        c2 = ChatService.start_conversation(founder, investor.id)
        assert c1.id == c2.id

    def test_creates_system_message_on_new_conversation(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        system_msg = Message.objects.filter(
            conversation=conversation, message_type=Message.MessageType.SYSTEM,
        ).first()
        assert system_msg is not None
        assert founder.first_name in system_msg.content
        assert investor.first_name in system_msg.content

    def test_raises_error_if_same_user(self, founder, match):
        with pytest.raises(ApplicationError) as exc:
            ChatService.start_conversation(founder, founder.id)
        assert exc.value.code == "SELF_CONVERSATION"

    def test_raises_error_if_user_not_found(self, founder):
        with pytest.raises(ApplicationError) as exc:
            ChatService.start_conversation(founder, 99999)
        assert exc.value.code == "NOT_FOUND"

    def test_raises_error_if_roles_not_investor_entrepreneur(self, match):
        user1 = UserFactory(role=User.Role.ADMIN)
        user2 = UserFactory(role=User.Role.MENTOR)
        with pytest.raises(ApplicationError) as exc:
            ChatService.start_conversation(user1, user2.id)
        assert exc.value.code == "INVALID_PARTICIPANTS"

    def test_raises_error_if_not_matched(self, founder, investor):
        with pytest.raises(ApplicationError) as exc:
            ChatService.start_conversation(founder, investor.id)
        assert exc.value.code == "NOT_MATCHED"


class TestSendMessage:
    def test_creates_message_in_conversation(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        msg = ChatService.send_message(founder, conversation.id, "text", "Hello!")
        assert msg.content == "Hello!"
        assert msg.message_type == "text"
        assert msg.sender == founder

    def test_raises_error_if_not_participant(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        stranger = UserFactory()
        with pytest.raises(ApplicationError) as exc:
            ChatService.send_message(stranger, conversation.id, "text", "Hi")
        assert exc.value.code == "FORBIDDEN"

    def test_raises_error_if_conversation_not_found(self, founder):
        with pytest.raises(ApplicationError) as exc:
            ChatService.send_message(founder, 99999, "text", "Hi")
        assert exc.value.code == "NOT_FOUND"

    def test_raises_error_if_conversation_closed(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        conversation.is_active = False
        conversation.save()
        with pytest.raises(ApplicationError) as exc:
            ChatService.send_message(founder, conversation.id, "text", "Hi")
        assert exc.value.code == "CONVERSATION_CLOSED"

    @patch("apps.notifications.services.NotificationService.notify")
    def test_sends_notification_to_other_participant(self, mock_notify, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "Hello!")
        assert mock_notify.called


class TestListConversations:
    def test_returns_user_conversations(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        convs = ChatService.list_conversations(founder)
        assert conversation.id in [c.id for c in convs]

    def test_includes_latest_message(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "Latest msg")
        convs = ChatService.list_conversations(founder)
        found = [c for c in convs if c.id == conversation.id][0]
        msgs = getattr(found, "latest_message", [])
        assert len(msgs) > 0
        assert msgs[0].content == "Latest msg"

    def test_does_not_return_other_users_conversations(self, founder, investor, match):
        ChatService.start_conversation(founder, investor.id)
        stranger = UserFactory()
        convs = ChatService.list_conversations(stranger)
        assert len(convs) == 0


class TestGetConversationMessages:
    def test_returns_paginated_messages(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        for i in range(5):
            ChatService.send_message(founder, conversation.id, "text", f"msg {i}")
        messages = ChatService.get_conversation_messages(founder, conversation.id, limit=3)
        assert len(messages) == 3

    def test_returns_newest_first(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "first")
        ChatService.send_message(founder, conversation.id, "text", "second")
        messages = ChatService.get_conversation_messages(founder, conversation.id)
        assert messages[0].content == "second"

    def test_before_cursor_pagination(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        msgs = []
        for i in range(5):
            msg = ChatService.send_message(founder, conversation.id, "text", f"msg {i}")
            msgs.append(msg)
        before = msgs[2].created_at.isoformat()
        result = ChatService.get_conversation_messages(
            founder, conversation.id, before=before, limit=10,
        )
        for m in result:
            assert m.created_at < msgs[2].created_at

    def test_raises_error_if_not_participant(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        stranger = UserFactory()
        with pytest.raises(ApplicationError) as exc:
            ChatService.get_conversation_messages(stranger, conversation.id)
        assert exc.value.code == "FORBIDDEN"


class TestMarkRead:
    def test_creates_read_status(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        msg = ChatService.send_message(founder, conversation.id, "text", "hello")
        ChatService.mark_read(investor, conversation.id)
        assert MessageReadStatus.objects.filter(message=msg, user=investor).exists()

    def test_idempotent(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "hello")
        ChatService.mark_read(investor, conversation.id)
        ChatService.mark_read(investor, conversation.id)


class TestUnreadCount:
    def test_returns_correct_count(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "msg 1")
        ChatService.send_message(founder, conversation.id, "text", "msg 2")
        count = ChatService.unread_count(investor)
        assert count == 2

    def test_returns_zero_after_read(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "msg 1")
        ChatService.mark_read(investor, conversation.id)
        count = ChatService.unread_count(investor)
        assert count == 0

    def test_does_not_count_own_messages(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        ChatService.send_message(founder, conversation.id, "text", "from founder")
        count_founder = ChatService.unread_count(founder)
        assert count_founder == 0


class TestGetConversation:
    def test_validates_participant_access(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        result = ChatService.get_conversation(founder, conversation.id)
        assert result.id == conversation.id

    def test_raises_error_for_non_participant(self, founder, investor, match):
        conversation = ChatService.start_conversation(founder, investor.id)
        stranger = UserFactory()
        with pytest.raises(ApplicationError) as exc:
            ChatService.get_conversation(stranger, conversation.id)
        assert exc.value.code == "FORBIDDEN"

    def test_raises_error_for_nonexistent(self, founder):
        with pytest.raises(ApplicationError) as exc:
            ChatService.get_conversation(founder, 99999)
        assert exc.value.code == "NOT_FOUND"
