# audiotherapy/urls.py
from django.urls import path
from .views import get_recommendations, list_disorders

urlpatterns = [
    path('recommendations/', get_recommendations, name='audio-recommendations'),
    path('disorders/',       list_disorders,      name='audio-disorders'),
]