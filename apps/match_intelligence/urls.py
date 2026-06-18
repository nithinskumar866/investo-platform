from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import MatchIntelligenceViewSet

router = DefaultRouter()
router.register(r"insights", MatchIntelligenceViewSet, basename="match-insight")

urlpatterns = router.urls
