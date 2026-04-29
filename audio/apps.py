# audiotherapy/apps.py
from django.apps import AppConfig


class AudioTherapyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audio'
    verbose_name = 'Audio Therapy'