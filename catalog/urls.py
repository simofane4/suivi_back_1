from rest_framework.routers import SimpleRouter

from .views import ActeDemanderViewSet, ActeFaitViewSet, MedicamentViewSet

router = SimpleRouter()
router.register("medicaments", MedicamentViewSet, basename="medicament")
router.register("actes-demandes", ActeDemanderViewSet, basename="acte-demande")
router.register("actes-faits", ActeFaitViewSet, basename="acte-fait")

urlpatterns = router.urls
