from django.contrib import admin

from .models import Assistant, Doctor


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cabinet", "specialiste", "inp", "phone", "gender")
    list_filter = ("cabinet", "specialiste", "gender")
    search_fields = ("user__first_name", "user__last_name", "user__username", "inp", "phone")
    autocomplete_fields = ("cabinet", "specialiste")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Nom")
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ("full_name", "cabinet", "cin", "phone", "gender")
    list_filter = ("cabinet", "gender")
    search_fields = ("user__first_name", "user__last_name", "user__username", "cin", "phone")
    autocomplete_fields = ("cabinet",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Nom")
    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
