from django.urls import path

from . import views

urlpatterns = [
    path("api/me/", views.my_profile, name="my_profile"),
]
