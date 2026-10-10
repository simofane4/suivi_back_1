from rest_framework.routers import SimpleRouter

from .views import (
    AllergieViewSet,
    AntecedentViewSet,
    ObservationViewSet,
    PatientFileViewSet,
    PatientViewSet,
)

router = SimpleRouter()
router.register("patients", PatientViewSet, basename="patient")
router.register("patient-files", PatientFileViewSet, basename="patient-file")
router.register("antecedents", AntecedentViewSet, basename="antecedent")
router.register("allergies", AllergieViewSet, basename="allergie")
router.register("observations", ObservationViewSet, basename="observation")

urlpatterns = router.urls