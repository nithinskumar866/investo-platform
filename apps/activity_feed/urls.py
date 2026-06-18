from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import FeedViewSet

router = DefaultRouter()
router.register(r"feed", FeedViewSet, basename="feed")

urlpatterns = router.urls
