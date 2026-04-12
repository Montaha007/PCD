from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SleepLogViewSet

router = DefaultRouter()
router.register(r'', SleepLogViewSet, basename='sleep-log')

urlpatterns = [
    path('', include(router.urls)),
]
