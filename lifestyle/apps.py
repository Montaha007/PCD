# lifestyle/apps.py
from django.apps import AppConfig


class LifestyleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lifestyle'
    verbose_name = 'Lifestyle Tracking'