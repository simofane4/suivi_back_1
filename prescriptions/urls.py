from rest_framework.routers import SimpleRouter

from .views import OrdonnanceViewSet

router = SimpleRouter()
router.register("ordonnances", OrdonnanceViewSet, basename="ordonnance")

urlpatterns = router.urls