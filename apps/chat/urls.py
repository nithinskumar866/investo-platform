from django.urls import path

from . import views

urlpatterns = [
    path("conversations/", views.conversation_list, name="chat-conversation-list"),
    path("conversations/<int:conversation_id>/", views.conversation_detail, name="chat-conversation-detail"),
    path("conversations/<int:conversation_id>/messages/", views.conversation_messages, name="chat-conversation-messages"),
    path("conversations/<int:conversation_id>/read/", views.mark_read, name="chat-mark-read"),
    path("unread-count/", views.unread_count, name="chat-unread-count"),
]
