from django.contrib import admin
from .models import *

# Register your models here.


admin.site.register(Doctor)
admin.site.register(Assistant)
admin.site.register(Specialite)
admin.site.register(Cabinet)
admin.site.register(Patient)
admin.site.register(PatientFile)
admin.site.register(ActeDemander)
admin.site.register(ActeFait)
admin.site.register(Medicament)
admin.site.register(Appointment)
admin.site.register(Ordonnance)
admin.site.register(Invoice)
