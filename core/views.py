from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthSerializer


class HealthView(APIView):
    """Liveness probe reporting database connectivity."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: HealthSerializer, 503: HealthSerializer})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database = "connected"
        except Exception:  # pragma: no cover - defensive
            database = "disconnected"

        healthy = database == "connected"
        return Response(
            {"status": "ok" if healthy else "error", "database": database},
            status=(
                status.HTTP_200_OK
                if healthy
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )
