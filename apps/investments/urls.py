from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"pipeline/investor", views.InvestorPipelineViewSet, basename="investor-pipeline")
router.register(r"pipeline/startup", views.StartupPipelineViewSet, basename="startup-pipeline")

urlpatterns = router.urls
