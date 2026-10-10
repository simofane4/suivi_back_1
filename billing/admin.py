from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "appointment", "date", "amount", "payed", "recipient")
    list_filter = ("payed", "date")
    search_fields = ("appointment__patient__firstname", "appointment__patient__lastname")
    autocomplete_fields = ("appointment", "recipient")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
