from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Cabinet, Specialite, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "cabinet", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "cabinet")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Rôle & cabinet", {"fields": ("role", "cabinet")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Rôle & cabinet", {"fields": ("role", "cabinet")}),
    )


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "address")
    search_fields = ("name", "number")


@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
