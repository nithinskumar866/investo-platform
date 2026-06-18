from django.urls import re_path

from apps.chat.consumers import ChatConsumer
from apps.notifications.consumers import NotificationConsumer
from apps.activity_feed.consumers import FeedConsumer
from apps.meetings.consumers import MeetingConsumer
from apps.investments.consumers import InvestmentConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/notifications/$", NotificationConsumer.as_asgi()),
    re_path(r"ws/feed/$", FeedConsumer.as_asgi()),
    re_path(r"ws/meetings/$", MeetingConsumer.as_asgi()),
    re_path(r"ws/investments/$", InvestmentConsumer.as_asgi()),
]
