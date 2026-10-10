from django.contrib import admin

from .models import (
    Allergie,
    Antecedent,
    Observation,
    Patient,
    PatientFile,
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("firstname", "lastname", "cin", "gender", "phone", "cabinet")
    search_fields = ("firstname", "lastname", "cin", "phone")
    list_filter = ("gender", "child", "cabinet")


@admin.register(PatientFile)
class PatientFileAdmin(admin.ModelAdmin):
    list_display = ("patient", "file", "uploaded_at")
    search_fields = ("patient__firstname", "patient__lastname", "file")


@admin.register(Antecedent)
class AntecedentAdmin(admin.ModelAdmin):
    list_display = ("label", "patient", "created_at")
    search_fields = ("label",)


@admin.register(Allergie)
class AllergieAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "patient")
    search_fields = ("name",)


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ("patient", "diagnostic", "version", "created_at")
    search_fields = ("diagnostic", "diagnostic_label")
    list_filter = ("created_at",)