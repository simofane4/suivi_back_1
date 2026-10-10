from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AssistantViewSet, DoctorViewSet, MeView, UserViewSet

app_name = "accounts"

router = DefaultRouter()
router.register("doctors", DoctorViewSet, basename="doctor")
router.register("assistants", AssistantViewSet, basename="assistant")
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    *router.urls,
]
