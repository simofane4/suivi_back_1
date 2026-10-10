from django.contrib import admin

from .models import Invoice, InvoiceItem, Payment


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "cabinet", "date", "amount", "payed", "status")
    list_filter = ("cabinet", "payed", "status")
    search_fields = ("appointment__patient__firstname", "appointment__patient__lastname")
    inlines = [InvoiceItemInline, PaymentInline]