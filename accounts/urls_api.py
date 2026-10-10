from rest_framework.routers import SimpleRouter

from .views import (
    AssistantViewSet,
    CabinetViewSet,
    DoctorViewSet,
    SpecialiteViewSet,
    UserViewSet,
)

router = SimpleRouter()
router.register("cabinets", CabinetViewSet, basename="cabinet")
router.register("specialites", SpecialiteViewSet, basename="specialite")
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("assistants", AssistantViewSet, basename="assistant")
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls
