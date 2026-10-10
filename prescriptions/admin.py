from django.contrib import admin

from .models import Ordonnance, OrdonnanceLine


class OrdonnanceLineInline(admin.TabularInline):
    model = OrdonnanceLine
    extra = 0


@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ("id", "cabinet", "appointment", "created_at")
    list_filter = ("cabinet",)
    inlines = [OrdonnanceLineInline]