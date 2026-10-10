"""Root URL configuration.

Every endpoint lives under /api/ and is produced by a per-app router. The
previous layout exposed ~40 individually written views at paths such as
`api/create-patient/`, `api/get-patient/` and `api/update-patient/<id>/`; those
are replaced by standard REST resources.
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from accounts.views import MeView, RoleTokenObtainPairView
from common.views import HealthView, api_root

auth_patterns = [
    path("token/", RoleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", MeView.as_view(), name="me"),
]

urlpatterns = [
    path("", RedirectView.as_view(url="/api/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api-root"),
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/", include((auth_patterns, "auth"))),
    path("api/", include("accounts.urls")),
    path("api/", include("cabinets.urls")),
    path("api/", include("patients.urls")),
    path("api/", include("clinical.urls")),
    path("api/", include("billing.urls")),
    # OpenAPI schema and interactive documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
