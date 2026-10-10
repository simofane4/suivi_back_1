from django.contrib import admin

from .models import (
    ActeDemander,
    ActeFait,
    Appointment,
    Medicament,
    Ordonnance,
    OrdonnanceMedicament,
)


class OrdonnanceMedicamentInline(admin.TabularInline):
    model = OrdonnanceMedicament
    extra = 0
    autocomplete_fields = ("medicament",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "cabinet", "date", "start", "end", "payed")
    list_filter = ("cabinet", "date", "payed")
    search_fields = ("patient__firstname", "patient__lastname", "description")
    autocomplete_fields = ("patient", "cabinet")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    ordering = ("-date", "start")


@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "cabinet", "created_at")
    list_filter = ("cabinet",)
    search_fields = ("description", "appointment__patient__lastname")
    autocomplete_fields = ("appointment", "cabinet", "acte_demander", "acte_fait")
    readonly_fields = ("created_at", "updated_at")
    inlines = (OrdonnanceMedicamentInline,)


@admin.register(ActeDemander)
class ActeDemanderAdmin(admin.ModelAdmin):
    list_display = ("title", "cabinet")
    list_filter = ("cabinet",)
    search_fields = ("title", "description")
    autocomplete_fields = ("cabinet",)


@admin.register(ActeFait)
class ActeFaitAdmin(admin.ModelAdmin):
    list_display = ("title", "cabinet")
    list_filter = ("cabinet",)
    search_fields = ("title", "description")
    autocomplete_fields = ("cabinet",)


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ("name", "cabinet")
    list_filter = ("cabinet",)
    search_fields = ("name", "description")
    autocomplete_fields = ("cabinet",)
