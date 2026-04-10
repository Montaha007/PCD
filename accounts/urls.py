from django.urls import path
from . import views
urlpatterns = [
    path('api/register/', views.register, name='register_user'),
    path('api/login/', views.login_user, name='login_user'),
    path('api/logout/', views.logout_user, name='logout_user'),
]