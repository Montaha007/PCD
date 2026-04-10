

from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Plugs our custom model into Django's admin
    while keeping the built-in password hashing UI.
    """

    model = CustomUser

    # Columns visible in the user list
    list_display  = ("email", "full_name", "gender", "country", "age",
                     "notifications_enabled", "is_staff", "is_active")
    list_filter   = ("gender", "is_staff", "is_active", "notifications_enabled")
    search_fields = ("email", "full_name", "country")
    ordering      = ("email",)

    # Detail page layout (fieldsets = collapsible sections)
    fieldsets = (
        ("Credentials",  {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name", "age", "gender", "country", "insomnia_duration_years")}),        ("Preferences",  {"fields": ("notifications_enabled",)}),
        ("Permissions",  {"fields": ("is_active", "is_staff", "is_superuser",
                                     "groups", "user_permissions")}),
        ("Dates",        {"fields": ("last_login", "date_joined")}),
    )

    # Layout for the "Add user" form in admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "age", "gender", "country", "insomnia_duration_years", "notifications_enabled","password1", "password2", "is_staff", "is_active"),
        }),
    )