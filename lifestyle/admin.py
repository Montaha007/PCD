# lifestyle/admin.py
from django.contrib import admin
from .models import LifestyleLog


@admin.register(LifestyleLog)
class LifestyleLogAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'date', 'WorkHours', 'CaffeineIntake',
        'PhoneTime', 'Work_x_Caffeine', 'Screen_Time_Intensity',
    )
    list_filter = ('date',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = (
        'Work_x_Caffeine', 'Screen_Time_Intensity',
        'created_at', 'updated_at',
    )
    date_hierarchy = 'date'