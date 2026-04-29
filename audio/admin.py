# audiotherapy/admin.py
from django.contrib import admin
from .models import DisorderRecommendation


@admin.register(DisorderRecommendation)
class DisorderRecommendationAdmin(admin.ModelAdmin):
    list_display = ('disorder', 'brainwave', 'priority', 'target_frequency_hz')
    list_filter = ('disorder', 'brainwave')
    ordering = ('disorder', 'priority')