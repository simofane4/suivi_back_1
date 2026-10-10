from django.contrib import admin

from .models import Cabinet, Specialite


@admin.register(Cabinet)
class CabinetAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "address", "created_at")
    search_fields = ("name", "number", "address")
    ordering = ("name",)


@admin.register(Specialite)
class SpecialiteAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
