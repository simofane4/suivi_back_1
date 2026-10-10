from rest_framework.routers import DefaultRouter

from .views import CabinetViewSet, SpecialiteViewSet

app_name = "cabinets"

router = DefaultRouter()
router.register("cabinets", CabinetViewSet, basename="cabinet")
router.register("specialites", SpecialiteViewSet, basename="specialite")

urlpatterns = router.urls
