from decimal import Decimal
from io import BytesIO

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

from core.mixins import CabinetScopedQuerysetMixin
from core.pdf import PAGE, draw_ar, new_pdf_response
from core.permissions import IsCabinetStaffOrAdmin
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import Invoice, Payment
from .serializers import InvoiceSerializer, PaymentSerializer


class InvoiceViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Invoice.objects.select_related(
        "cabinet", "appointment__patient", "recipient"
    )
    serializer_class = InvoiceSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "appointment__patient__firstname",
        "appointment__patient__lastname",
    ]
    ordering_fields = ["date", "amount", "created_at"]
    cabinet_field = "appointment__cabinet"

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        paid = params.get("payed", "").strip().lower()
        if paid in ("1", "true", "yes", "0", "false", "no"):
            queryset = queryset.filter(payed=paid in ("1", "true", "yes"))

        status = params.get("status", "").strip()
        if status:
            queryset = queryset.filter(status=status)

        appointment = params.get("appointment", "").strip()
        if appointment:
            queryset = queryset.filter(appointment_id=appointment)

        date_from = (
            params.get("start_date", "").strip()
            or params.get("date_from", "").strip()
        )
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        date_to = params.get("date_to", "").strip()
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset.prefetch_related("items", "payments")

    @action(detail=False, methods=["get"], url_path="unpaid")
    def unpaid(self, request):
        """List the invoices that are not fully paid yet (API.md contract)."""
        queryset = self.filter_queryset(self.get_queryset().filter(payed=False))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=True, methods=["post"], url_path="payments")
    def add_payment(self, request, pk=None):
        invoice = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = Payment.objects.create(
            invoice=invoice,
            created_by=request.user,
            paid_at=timezone.now(),
            **serializer.validated_data,
        )
        invoice.refresh_status()
        return Response(PaymentSerializer(payment).data, status=201)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        invoice = self.get_object()
        stream = BytesIO()
        render_invoice_pdf(stream, invoice)
        stream.seek(0)
        return new_pdf_response(stream, f"facture_{invoice.pk}.pdf")


def _format(amount: Decimal) -> str:
    return f"{amount:.2f}"


def render_invoice_pdf(stream, invoice):
    cabinet = invoice.cabinet
    c = pdf_canvas.Canvas(stream, pagesize=PAGE)
    width, height = PAGE
    margin = 20 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - 25 * mm, cabinet.name)
    c.setFont("Helvetica", 10)
    y = height - 35 * mm
    if cabinet.address:
        c.drawString(margin, y, cabinet.address)
        y -= 5 * mm
    if cabinet.number:
        c.drawString(margin, y, f"N° registre : {cabinet.number}")
    draw_ar(c, width - margin, height - 30 * mm, "فاتورة", 16)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - 55 * mm, "FACTURE")
    c.line(margin, height - 60 * mm, width - margin, height - 60 * mm)

    c.setFont("Helvetica", 11)
    local_date = timezone.localtime(invoice.date)
    c.drawString(margin, height - 72 * mm, f"N° {invoice.pk}")
    c.drawString(width * 0.55, height - 72 * mm, f"Date : {local_date:%d/%m/%Y %H:%M}")
    c.drawString(margin, height - 80 * mm, f"Patient : {invoice.patient}")
    c.drawString(width * 0.55, height - 80 * mm, f"Reçu par : {invoice.recipient.username if invoice.recipient_id else '-'}")

    y = height - 100 * mm
    c.setFillColor(colors.Color(0.94, 0.94, 0.94))
    c.rect(margin, y - 5 * mm, width - 2 * margin, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin + 2 * mm, y - 3 * mm, "Désignation")
    c.drawRightString(width - margin - 2 * mm, y - 3 * mm, "Montant")
    y -= 12 * mm

    items = list(invoice.items.all())
    rows = [(item.label, item.amount) for item in items] or [
        ("Consultation", invoice.amount)
    ]
    c.setFont("Helvetica", 10)
    for label, amount in rows:
        c.drawString(margin + 2 * mm, y, label)
        c.drawRightString(width - margin - 2 * mm, y, _format(amount))
        y -= 6 * mm

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 11)
    lines = [
        ("Total", invoice.amount),
        ("Part organisme", invoice.organisme_share),
        ("Part patient", invoice.patient_share),
        ("Payé organisme", invoice.organisme_paid),
        ("Payé patient", invoice.patient_paid),
        ("Reste organisme", invoice.organisme_rest),
        ("Reste patient", invoice.patient_rest),
    ]
    for label, amount in lines:
        c.setFont("Helvetica-Bold" if label == "Total" else "Helvetica", 11)
        c.drawString(width * 0.6, y, label)
        c.drawRightString(width - margin, y, _format(amount))
        y -= 5.5 * mm

    status_label = dict(Invoice.Status.choices).get(invoice.status, invoice.status)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, 40 * mm, f"Statut : {status_label}")
    c.showPage()
    c.save()