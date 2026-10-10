from rest_framework.routers import DefaultRouter

from .views import PatientFileViewSet, PatientViewSet

app_name = "patients"

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="patient")
router.register(
    "patient-files",
    PatientFileViewSet,
    basename="patientfile",
)

urlpatterns = router.urls
