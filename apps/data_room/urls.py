from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DataRoomViewSet, DataRoomDocumentViewSet, InvestorDocumentViewSet

router = DefaultRouter()
router.register(r"rooms", DataRoomViewSet, basename="data-room")
router.register(r"documents", DataRoomDocumentViewSet, basename="data-room-document")
router.register(r"investor/documents", InvestorDocumentViewSet, basename="investor-document")

urlpatterns = router.urls
