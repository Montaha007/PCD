from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ("user", "timezone", "language", "updated_at")
	search_fields = ("user__email", "user__full_name", "timezone", "language")
