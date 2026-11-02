from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AvailabilityViewSet, MeetingViewSet

router = DefaultRouter()
router.register(r"", MeetingViewSet, basename="meeting")

urlpatterns = [
    path("availability/", AvailabilityViewSet.as_view({"get": "list", "post": "create"}), name="availability"),
] + router.urls
