from datetime import datetime, time as dtime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from billing.models import Invoice
from core.factories import Factories

URL = "/api/dashboard/stats/"


class DashboardTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.doc_user, self.doctor = self.factories.doctor("doc1", self.cab1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def test_stats_require_authentication(self):
        anon = APIClient()
        self.assertEqual(anon.get(URL).status_code, 401)

    def test_empty_cabinet_stats(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cabinet"], {"id": self.cab1.id})
        self.assertEqual(response.data["patients_total"], 0)
        self.assertEqual(response.data["appointments_today"], 0)
        self.assertEqual(len(response.data["patients_trend"]), 6)

    def test_stats_reflect_cabinet_data(self):
        patient = self.factories.patient(self.cab1, "BE123456")
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, dtime(12, 0)))
        appointment = Appointment.objects.create(
            cabinet=self.cab1,
            patient=patient,
            doctor=self.doctor,
            start=start,
            end=start + timezone.timedelta(hours=1),
            reason="Consultation",
        )
        self.client.post(
            "/api/invoices/",
            {
                "appointment": appointment.id,
                "amount": "500.00",
            },
            format="json",
        )
        response = self.client.get(URL)
        self.assertEqual(response.data["patients_total"], 1)
        self.assertEqual(response.data["patients_month"], 1)
        self.assertEqual(response.data["appointments_today"], 1)
        self.assertEqual(len(response.data["rdv_today"]), 1)
        self.assertEqual(
            response.data["rdv_today"][0]["patient_name"], "Ahmed Benali"
        )
        self.assertEqual(response.data["unpaid_invoices"], 1)
        self.assertEqual(response.data["reliquats_total"] > 0, True)

    def test_staff_stats_stay_scoped_to_own_cabinet(self):
        other_user, _ = self.factories.doctor("doc2", self.cab2)
        self.factories.patient(self.cab2, "ZZ000000")
        client = APIClient()
        client.force_authenticate(user=other_user)
        response = client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cabinet"], {"id": self.cab2.id})
        self.assertEqual(response.data["patients_total"], 1)

    def test_admin_can_query_any_cabinet(self):
        self.factories.patient(self.cab1, "BE111111")
        self.factories.patient(self.cab2, "ZZ222222")
        admin_user = self.factories.admin("boss")
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.get(URL, {"cabinet": self.cab2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patients_total"], 1)


class HealthTests(TestCase):
    def test_health_is_open_and_ok(self):
        client = APIClient()
        response = client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database"], "connected")


class ErrorEnvelopeTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.doc_user, _ = self.factories.doctor("doc1", self.cab1)
        self.patient = self.factories.patient(self.cab1, "BE123456")
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def test_validation_error_envelope(self):
        response = self.client.post(
            "/api/patients/",
            {
                "cin": self.patient.cin,
                "firstname": "X",
                "lastname": "Y",
                "gender": "Male",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["status"], 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")
        self.assertIn("cin", response.data["error"]["fields"])

    def test_unauthorized_envelope(self):
        client = APIClient()
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"]["code"], "unauthorized")

    def test_not_found_envelope(self):
        response = self.client.get("/api/patients/999999/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"]["code"], "not_found")


class DashboardAdminEdgeTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.admin = self.factories.admin("superadmin")
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_admin_without_cabinet_param_gets_null_cabinet(self):
        response = self.client.get(URL)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["cabinet"])
        self.assertEqual(response.data["patients_total"], 0)


class PdfHelperTests(TestCase):
    def test_draw_ar_handles_long_arabic_text(self):
        from io import BytesIO

        from reportlab.pdfgen import canvas as pdf_canvas

        from core.pdf import PAGE, draw_ar

        stream = BytesIO()
        c = pdf_canvas.Canvas(stream, pagesize=PAGE)
        long_arabic = (
            "وصفة طبية طويلة مع عدة كلمات عربية للتحقق من إعادة تشكيل "
            "الحروف ولف الأسطر بشكل صحيح في مستند PDF"
        )
        draw_ar(c, 400, 500, long_arabic, 12)
        c.save()
        self.assertTrue(stream.getvalue().startswith(b"%PDF"))

    def test_new_pdf_response_content_type(self):
        from io import BytesIO

        from core.pdf import new_pdf_response

        response = new_pdf_response(BytesIO(b"%PDF-test"), "doc.pdf")
        self.assertEqual(response["Content-Type"], "application/pdf")