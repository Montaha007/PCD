# lifestyle/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LifestyleLogViewSet

router = DefaultRouter()
router.register(r'logs', LifestyleLogViewSet, basename='lifestyle-log')

urlpatterns = [
    path('', include(router.urls)),
]