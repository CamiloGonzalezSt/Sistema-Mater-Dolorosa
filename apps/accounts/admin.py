from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'rut', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'rut', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = UserAdmin.fieldsets + (
        ('Datos institucionales', {'fields': ('rut', 'phone', 'role', 'foto')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos institucionales', {'fields': ('email', 'rut', 'phone', 'role')}),
    )
