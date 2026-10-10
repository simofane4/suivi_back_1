from rest_framework.routers import DefaultRouter

from .views import (
    ActeDemanderViewSet,
    ActeFaitViewSet,
    AppointmentViewSet,
    MedicamentViewSet,
    OrdonnanceViewSet,
)

app_name = "clinical"

router = DefaultRouter()
router.register("actes-demandes", ActeDemanderViewSet, basename="actedemander")
router.register("actes-faits", ActeFaitViewSet, basename="actefait")
router.register("medicaments", MedicamentViewSet, basename="medicament")
router.register("appointments", AppointmentViewSet, basename="appointment")
router.register("ordonnances", OrdonnanceViewSet, basename="ordonnance")

urlpatterns = router.urls
