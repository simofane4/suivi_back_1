from django.contrib import admin

from .models import ActeDemander, ActeFait, Medicament


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ("name", "cabinet", "created_at")
    search_fields = ("name",)
    list_filter = ("cabinet",)


@admin.register(ActeDemander)
class ActeDemanderAdmin(admin.ModelAdmin):
    list_display = ("title", "cabinet", "created_at")
    search_fields = ("title",)
    list_filter = ("cabinet",)


@admin.register(ActeFait)
class ActeFaitAdmin(admin.ModelAdmin):
    list_display = ("title", "cabinet", "created_at")
    search_fields = ("title",)
    list_filter = ("cabinet",)
