from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "start", "end", "patient", "doctor", "status")
    list_filter = ("status", "cabinet", "date")
    search_fields = ("patient__firstname", "patient__lastname", "reason")
    ordering = ("-start",)