from datetime import datetime

from django.db import connection
from django.db.models import Sum, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from appointments.models import Appointment
from billing.models import Invoice, Payment
from core.permissions import ADMIN, IsCabinetStaffOrAdmin
from patients.models import Patient

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


def _shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    month += delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def _month_bounds(year: int, month: int):
    start = timezone.make_aware(datetime(year, month, 1))
    end_year, end_month = _shift_month(year, month, 1)
    end = timezone.make_aware(datetime(end_year, end_month, 1))
    return start, end


class DashboardStatsView(APIView):
    """KPI bundle for a cabinet: patients, today's agenda, revenue, leftovers."""

    permission_classes = [IsCabinetStaffOrAdmin]

    def _cabinet(self, request):
        user = request.user
        if user.is_superuser or getattr(user, "role", None) == ADMIN:
            cabinet_id = request.query_params.get("cabinet", "").strip()
            return cabinet_id or user.cabinet_id
        return user.cabinet_id

    @extend_schema(
        responses={
            200: inline_serializer(
                "DashboardStats",
                fields={
                    "cabinet": drf_serializers.IntegerField(),
                    "patients_total": drf_serializers.IntegerField(),
                    "patients_month": drf_serializers.IntegerField(),
                    "patients_trend": drf_serializers.ListField(
                        child=inline_serializer(
                            "MonthTrend",
                            fields={
                                "month": drf_serializers.CharField(),
                                "count": drf_serializers.IntegerField(),
                            },
                        )
                    ),
                    "appointments_today": drf_serializers.IntegerField(),
                    "rdv_today": drf_serializers.ListField(
                        child=inline_serializer(
                            "RdvToday",
                            fields={
                                "id": drf_serializers.IntegerField(),
                                "start": drf_serializers.CharField(),
                                "end": drf_serializers.CharField(),
                                "patient_name": drf_serializers.CharField(),
                                "doctor_name": drf_serializers.CharField(
                                    allow_null=True
                                ),
                                "status": drf_serializers.CharField(),
                            },
                        )
                    ),
                    "rdv_status": drf_serializers.ListField(
                        child=inline_serializer(
                            "RdvStatus",
                            fields={
                                "status": drf_serializers.CharField(),
                                "count": drf_serializers.IntegerField(),
                            },
                        )
                    ),
                    "invoiced_month": drf_serializers.DecimalField(
                        max_digits=14, decimal_places=2
                    ),
                    "revenue_month": drf_serializers.DecimalField(
                        max_digits=14, decimal_places=2
                    ),
                    "unpaid_invoices": drf_serializers.IntegerField(),
                    "reliquats_patient": drf_serializers.DecimalField(
                        max_digits=14, decimal_places=2
                    ),
                    "reliquats_organisme": drf_serializers.DecimalField(
                        max_digits=14, decimal_places=2
                    ),
                    "reliquats_total": drf_serializers.DecimalField(
                        max_digits=14, decimal_places=2
                    ),
                },
            )
        }
    )
    def get(self, request):
        cabinet_id = self._cabinet(request)
        cabinet = {"id": int(cabinet_id)} if cabinet_id else None

        patients = (
            Patient.objects.filter(cabinet_id=cabinet_id)
            if cabinet_id
            else Patient.objects.none()
        )
        appointments = (
            Appointment.objects.filter(cabinet_id=cabinet_id)
            if cabinet_id
            else Appointment.objects.none()
        )
        invoices = (
            Invoice.objects.filter(cabinet_id=cabinet_id)
            if cabinet_id
            else Invoice.objects.none()
        )
        payments = (
            Payment.objects.filter(invoice__cabinet_id=cabinet_id)
            if cabinet_id
            else Payment.objects.none()
        )

        now = timezone.now()
        today = timezone.localdate(now)
        month_year, month = today.year, today.month
        month_start, month_end = _month_bounds(month_year, month)

        patients_total = patients.count()
        patients_month = patients.filter(created_at__gte=month_start).count()

        trend = []
        for i in range(5, -1, -1):
            y, m = _shift_month(month_year, month, -i)
            start, end = _month_bounds(y, m)
            trend.append(
                {
                    "month": f"{y:04d}-{m:02d}",
                    "count": patients.filter(created_at__gte=start, created_at__lt=end).count(),
                }
            )

        rdv_today = list(
            appointments.filter(date=today)
            .select_related("patient", "doctor__user")
            .order_by("start")
        )
        rdv_today_payload = [
            {
                "id": rdv.id,
                "start": rdv.start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "end": rdv.end.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "patient_name": str(rdv.patient),
                "doctor_name": str(rdv.doctor) if rdv.doctor_id else None,
                "status": rdv.status,
            }
            for rdv in rdv_today
        ]

        rdv_status = list(
            appointments.exclude(status=Appointment.Status.CANCELLED)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        invoiced = (
            invoices.filter(
                date__gte=month_start, date__lt=month_end
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )
        revenue = (
            payments.filter(paid_at__gte=month_start, paid_at__lt=month_end).aggregate(
                total=Sum("amount")
            )["total"]
            or 0
        )

        unpaid = invoices.exclude(status=Invoice.Status.PAID).prefetch_related("payments")
        reliquats_patient = 0
        reliquats_organisme = 0
        unpaid_count = unpaid.count()
        for invoice in unpaid:
            reliquats_patient += invoice.patient_rest
            reliquats_organisme += invoice.organisme_rest

        return Response(
            {
                "cabinet": cabinet,
                "patients_total": patients_total,
                "patients_month": patients_month,
                "patients_trend": trend,
                "appointments_today": len(rdv_today),
                "rdv_today": rdv_today_payload,
                "rdv_status": [
                    {"status": row["status"], "count": row["count"]}
                    for row in rdv_status
                ],
                "invoiced_month": invoiced,
                "revenue_month": revenue,
                "unpaid_invoices": unpaid_count,
                "reliquats_patient": reliquats_patient,
                "reliquats_organisme": reliquats_organisme,
                "reliquats_total": reliquats_patient + reliquats_organisme,
            }
        )
