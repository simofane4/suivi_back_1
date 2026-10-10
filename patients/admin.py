from django.contrib import admin

from .models import Patient, PatientFile


class PatientFileInline(admin.TabularInline):
    model = PatientFile
    extra = 0
    fields = ("file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cin", "phone", "gender", "age", "cabinet")
    list_filter = ("cabinet", "gender", "child")
    search_fields = ("firstname", "lastname", "cin", "phone")
    autocomplete_fields = ("cabinet",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (PatientFileInline,)
    ordering = ("lastname", "firstname")

    @admin.display(description="Nom", ordering="lastname")
    def full_name(self, obj):
        return f"{obj.firstname} {obj.lastname}".strip()


@admin.register(PatientFile)
class PatientFileAdmin(admin.ModelAdmin):
    list_display = ("patient", "file", "uploaded_at")
    search_fields = ("patient__firstname", "patient__lastname")
    autocomplete_fields = ("patient",)
    readonly_fields = ("uploaded_at",)
