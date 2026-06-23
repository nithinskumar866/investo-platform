import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.chat.models import Conversation, ConversationParticipant, Message, MessageReadStatus
from apps.common.tests.factories import UserFactory, FounderFactory, InvestorFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def founder():
    return FounderFactory()


@pytest.fixture
def investor():
    return InvestorFactory()


class TestConversation:
    def test_create_conversation(self, user):
        conversation = Conversation.objects.create(created_by=user)
        assert conversation.id is not None
        assert conversation.is_active is True
        assert conversation.created_by == user

    def test_conversation_str(self, user):
        conversation = Conversation.objects.create(created_by=user)
        assert str(conversation) == f"Conversation {conversation.id}"

    def test_conversation_participant_association(self, user, founder, investor):
        conversation = Conversation.objects.create(created_by=user)
        ConversationParticipant.objects.create(conversation=conversation, user=founder)
        ConversationParticipant.objects.create(conversation=conversation, user=investor)
        assert conversation.participants.count() == 2
        assert founder.chat_participations.count() == 1
        assert investor.chat_participations.count() == 1

    def test_conversation_ordering_by_updated_at(self, user):
        c1 = Conversation.objects.create(created_by=user)
        c2 = Conversation.objects.create(created_by=user)
        assert list(Conversation.objects.all()) == [c2, c1]

    def test_conversation_updated_at_changes_on_message(self, user):
        conversation = Conversation.objects.create(created_by=user)
        old_updated = conversation.updated_at
        Message.objects.create(
            conversation=conversation, sender=user,
            message_type=Message.MessageType.TEXT, content="hello",
        )
        conversation.refresh_from_db()
        assert conversation.updated_at >= old_updated


class TestConversationParticipant:
    def test_unique_constraint(self, user, founder):
        conversation = Conversation.objects.create(created_by=user)
        ConversationParticipant.objects.create(conversation=conversation, user=founder)
        with pytest.raises(IntegrityError):
            ConversationParticipant.objects.create(conversation=conversation, user=founder)

    def test_str(self, user):
        conversation = Conversation.objects.create(created_by=user)
        participant = ConversationParticipant.objects.create(
            conversation=conversation, user=user,
        )
        assert str(participant) == f"{user.email} in {conversation.id}"


class TestMessage:
    def test_create_text_message(self, user):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user,
            message_type=Message.MessageType.TEXT,
            content="Hello, world!",
        )
        assert message.message_type == "text"
        assert message.content == "Hello, world!"
        assert message.sender == user

    def test_create_file_message(self, user):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user,
            message_type=Message.MessageType.FILE,
            metadata={"filename": "doc.pdf", "size": 1024},
        )
        assert message.message_type == "file"

    def test_create_system_message(self, user):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user,
            message_type=Message.MessageType.SYSTEM,
            content="Conversation started",
        )
        assert message.message_type == "system"

    def test_message_str_truncation(self, user):
        conversation = Conversation.objects.create(created_by=user)
        long_content = "x" * 100
        message = Message.objects.create(
            conversation=conversation, sender=user,
            content=long_content,
        )
        expected = f"{user.email}: {long_content[:50]}"
        assert str(message) == expected

    def test_message_default_type_is_text(self, user):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user, content="hi",
        )
        assert message.message_type == Message.MessageType.TEXT

    def test_message_ordering(self, user):
        conversation = Conversation.objects.create(created_by=user)
        m1 = Message.objects.create(conversation=conversation, sender=user, content="first")
        m2 = Message.objects.create(conversation=conversation, sender=user, content="second")
        messages = Message.objects.filter(conversation=conversation).order_by("-created_at")
        assert list(messages) == [m2, m1]

    def test_message_default_metadata(self, user):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user, content="test",
        )
        assert message.metadata == {}


class TestMessageReadStatus:
    def test_create_read_status(self, user, investor):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user, content="test",
        )
        read_status = MessageReadStatus.objects.create(
            message=message, user=investor,
        )
        assert read_status.user == investor
        assert read_status.message == message
        assert read_status.read_at is not None

    def test_unique_constraint(self, user, investor):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user, content="test",
        )
        MessageReadStatus.objects.create(message=message, user=investor)
        with pytest.raises(IntegrityError):
            MessageReadStatus.objects.create(message=message, user=investor)

    def test_str(self, user, investor):
        conversation = Conversation.objects.create(created_by=user)
        message = Message.objects.create(
            conversation=conversation, sender=user, content="test",
        )
        read_status = MessageReadStatus.objects.create(message=message, user=investor)
        assert str(read_status) == f"{investor.email} read {message.id}"
