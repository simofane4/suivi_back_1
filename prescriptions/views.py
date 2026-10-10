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

from .models import Ordonnance
from .serializers import OrdonnanceSerializer


class OrdonnanceViewSet(CabinetScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Ordonnance.objects.select_related(
        "cabinet", "appointment__patient", "acte_demander", "acte_fait"
    )
    serializer_class = OrdonnanceSerializer
    permission_classes = [IsCabinetStaffOrAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["description", "appointment__patient__firstname",
                     "appointment__patient__lastname"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        appointment = self.request.query_params.get("appointment", "").strip()
        if appointment:
            queryset = queryset.filter(appointment_id=appointment)
        medicament = self.request.query_params.get("medicament", "").strip()
        if medicament:
            queryset = queryset.filter(lines__medicament_id=medicament).distinct()
        patient = self.request.query_params.get("patient", "").strip()
        if patient:
            queryset = queryset.filter(appointment__patient_id=patient)
        return queryset.prefetch_related("lines__medicament")

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        ordonnance = self.get_object()
        stream = BytesIO()
        render_ordonnance_pdf(stream, ordonnance)
        stream.seek(0)
        return new_pdf_response(stream, f"ordonnance_{ordonnance.pk}.pdf")


def render_ordonnance_pdf(stream, ordonnance):
    cabinet = ordonnance.cabinet
    patient = (
        ordonnance.appointment.patient
        if ordonnance.appointment_id else None
    )
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
    draw_ar(c, width - margin, height - 30 * mm, "وصفة طبية", 16)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, height - 55 * mm, "ORDONNANCE")
    c.setStrokeColor(colors.black)
    c.line(margin, height - 60 * mm, width - margin, height - 60 * mm)

    c.setFont("Helvetica", 11)
    row_y = height - 72 * mm
    if patient:
        c.drawString(margin, row_y, f"Patient : {patient}")
    if ordonnance.created_at:
        created = timezone.localtime(ordonnance.created_at)
        c.drawString(
            width * 0.55,
            row_y,
            f"Date : {created:%d/%m/%Y %H:%M}",
        )
    row_y -= 8 * mm
    if ordonnance.acte_demander:
        c.drawString(margin, row_y, f"Acte demandé : {ordonnance.acte_demander.title}")
        row_y -= 6 * mm
    if ordonnance.acte_fait:
        c.drawString(margin, row_y, f"Acte fait : {ordonnance.acte_fait.title}")
        row_y -= 6 * mm
    row_y -= 4 * mm

    lines = list(ordonnance.lines.select_related("medicament"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, row_y, "Médicaments")
    c.setFillColor(colors.Color(0.94, 0.94, 0.94))
    c.rect(margin, row_y - 5 * mm, width - 2 * margin, 7 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.drawString(margin + 2 * mm, row_y - 3 * mm, "Médicament")
    c.drawString(width * 0.55, row_y - 3 * mm, "Dosage")
    c.drawString(width * 0.78, row_y - 3 * mm, "Durée")
    row_y -= 12 * mm

    c.setFont("Helvetica", 10)
    for line in lines:
        c.drawString(margin + 2 * mm, row_y, line.medicament.name_fr or line.medicament.name)
        c.drawString(width * 0.55, row_y, line.dosage or "")
        c.drawString(width * 0.78, row_y, line.duration or "")
        row_y -= 6 * mm
        if row_y < 25 * mm:
            c.showPage()
            row_y = height - 25 * mm

    if ordonnance.description:
        row_y -= 8 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(margin, row_y, "Consignes")
        c.setFont("Helvetica", 10)
        block = ordonnance.description
        lines_wrapped = []
        line = ""
        for word in block.split():
            if c.stringWidth(line + word, "Helvetica", 10) < width - 2 * margin:
                line = f"{line} {word}".strip()
            else:
                lines_wrapped.append(line)
                line = word
        if line:
            lines_wrapped.append(line)
        row_y -= 6 * mm
        for wrapped in lines_wrapped:
            c.drawString(margin, row_y, wrapped)
            row_y -= 5 * mm

    if patient and ordonnance.appointment and ordonnance.appointment.doctor_id:
        doctor = ordonnance.appointment.doctor
        c.setFont("Helvetica", 10)
        c.drawRightString(
            width - margin,
            35 * mm,
            doctor.user.get_full_name() or doctor.user.username,
        )
        c.drawRightString(width - margin, 31 * mm, "Signature du médecin")
    c.showPage()
    c.save()