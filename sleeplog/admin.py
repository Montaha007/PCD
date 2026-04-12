from django.contrib import admin
from .models import SleepLog


@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'sleep_time', 'wake_up_time', 'calculated_sleep_duration', 'satisfaction_of_sleep', 'created_at']
    list_filter = ['satisfaction_of_sleep', 'late_night_sleep', 'created_at']
    search_fields = ['user__email', 'user__full_name']
    readonly_fields = ['calculated_sleep_duration', 'duration_of_problems', 'created_at']
