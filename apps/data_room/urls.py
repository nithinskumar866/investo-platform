from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccessRequestViewSet,
    DataRoomDocumentViewSet,
    DataRoomViewSet,
    InvestorDocumentViewSet,
    InvestorRoomViewSet,
)

router = DefaultRouter()
router.register(r"rooms", DataRoomViewSet, basename="data-room")
router.register(r"documents", DataRoomDocumentViewSet, basename="data-room-document")
router.register(r"investor/documents", InvestorDocumentViewSet, basename="investor-document")

router.register(r"investor/rooms", InvestorRoomViewSet, basename="investor-room")
router.register(r"access-requests", AccessRequestViewSet, basename="access-request")

urlpatterns = router.urls
