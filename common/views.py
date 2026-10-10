"""Shared API views: health check and the resource index."""

from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView


class HealthView(APIView):
    """Liveness probe. Replaces the old `/hello/`, which crashed for any user
    without a linked doctor profile."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request):
        database_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_ok = False

        return Response(
            {
                "status": "ok" if database_ok else "degraded",
                "database": "ok" if database_ok else "unavailable",
            },
            status=status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


# (path segment, reverse name) for the resource index.
RESOURCES = (
    ("cabinets", "cabinets:cabinet-list"),
    ("specialites", "cabinets:specialite-list"),
    ("doctors", "accounts:doctor-list"),
    ("assistants", "accounts:assistant-list"),
    ("patients", "patients:patient-list"),
    ("patient-files", "patients:patientfile-list"),
    ("actes-demandes", "clinical:actedemander-list"),
    ("actes-faits", "clinical:actefait-list"),
    ("medicaments", "clinical:medicament-list"),
    ("appointments", "clinical:appointment-list"),
    ("ordonnances", "clinical:ordonnance-list"),
    ("invoices", "billing:invoice-list"),
)


class ApiRootView(APIView):
    """Index of the main resources."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request):
        return Response(
            {
                name: reverse(reverse_name, request=request, format="json")
                for name, reverse_name in RESOURCES
            },
            status=status.HTTP_200_OK,
        )


api_root = ApiRootView.as_view()
