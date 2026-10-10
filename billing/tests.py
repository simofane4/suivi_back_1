from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from billing.models import Invoice, Payment
from core.factories import (
    Factories,
    future_start,
    make_start_end,
    to_iso,
)


class BillingTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        doc_user, self.doctor = self.factories.doctor("doc1", self.cab1)
        self.apiuser = doc_user
        self.patient_cnops = self.factories.patient(
            self.cab1, "BE123456", assurance="CNOPS"
        )
        self.patient_none = self.factories.patient(
            self.cab1, "BE654321", lastname="Zerhouni", assurance=""
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.apiuser)
        self._slot = 0

    def _appointment(self, patient) -> dict:
        self._slot += 3
        start, end = make_start_end(future_start(self._slot))
        return self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "doctor": self.doctor.id,
                "start": to_iso(start),
                "end": to_iso(end),
                "reason": "Consultation",
            },
            format="json",
        ).data

    def _invoice(self, patient, amount="500.00", items=True):
        appointment = self._appointment(patient)
        payload = {
            "appointment": appointment["id"],
            "amount": amount,
        }
        if items:
            payload["items"] = [
                {"label": "Consultation", "amount": amount}
            ]
        response = self.client.post(
            "/api/invoices/", payload, format="json"
        )
        self.assertEqual(response.status_code, 201)
        return response.data

    def test_cnops_ratio_applied_by_default(self):
        data = self._invoice(self.patient_cnops)
        self.assertEqual(Decimal(data["organisme_ratio"]), Decimal("80"))
        self.assertEqual(Decimal(data["organisme_share"]), Decimal("400.00"))
        self.assertEqual(Decimal(data["patient_share"]), Decimal("100.00"))
        self.assertEqual(data["status"], "unpaid")

    def test_no_assurance_defaults_to_patient_share(self):
        data = self._invoice(self.patient_none)
        self.assertEqual(Decimal(data["organisme_ratio"]), Decimal("0"))
        self.assertEqual(Decimal(data["patient_share"]), Decimal("500.00"))

    def test_partial_payment_updates_status(self):
        data = self._invoice(self.patient_cnops)
        url = f"/api/invoices/{data['id']}/payments/"
        response = self.client.post(
            url,
            {"amount": "50.00", "kind": "patient", "method": "cash"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        fresh = self.client.get(f"/api/invoices/{data['id']}/").data
        self.assertEqual(fresh["status"], "partially_paid")
        self.assertEqual(Decimal(fresh["patient_paid"]), Decimal("50.00"))
        self.assertEqual(Decimal(fresh["patient_rest"]), Decimal("50.00"))

    def test_insurance_and_patient_shares_pay_off_invoice(self):
        data = self._invoice(self.patient_cnops)
        url = f"/api/invoices/{data['id']}/payments/"
        self.client.post(
            url,
            {"amount": "400.00", "kind": "organisme", "method": "cheque"},
            format="json",
        )
        self.client.post(
            url,
            {"amount": "100.00", "kind": "patient", "method": "card"},
            format="json",
        )
        fresh = self.client.get(f"/api/invoices/{data['id']}/").data
        self.assertEqual(fresh["status"], "paid")
        self.assertEqual(fresh["payed"], True)
        self.assertEqual(Decimal(fresh["patient_rest"]), Decimal("0"))
        self.assertEqual(Decimal(fresh["organisme_rest"]), Decimal("0"))

    def test_unpaid_action_lists_only_open_invoices(self):
        paid = self._invoice(self.patient_cnops, amount="200.00")
        self.client.post(
            f"/api/invoices/{paid['id']}/payments/",
            {"amount": "200.00", "kind": "patient", "method": "cash"},
            format="json",
        )
        unpaid = self._invoice(self.patient_none, amount="300.00")
        response = self.client.get("/api/invoices/unpaid/")
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {unpaid["id"]})

    def test_payment_must_be_positive(self):
        data = self._invoice(self.patient_cnops)
        response = self.client.post(
            f"/api/invoices/{data['id']}/payments/",
            {"amount": "0", "kind": "patient", "method": "cash"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_refresh_status_marks_paid(self):
        appointment_id = self._appointment(self.patient_cnops)["id"]
        invoice = Invoice.objects.create(
            cabinet=self.cab1,
            appointment_id=appointment_id,
            amount=Decimal("100.00"),
            recipient=self.apiuser,
        )
        Payment.objects.create(
            invoice=invoice,
            amount=Decimal("100.00"),
            kind=Payment.Kind.PATIENT,
            created_by=self.apiuser,
        )
        invoice.refresh_status()
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        self.assertTrue(invoice.payed)

    def test_invoice_floats_are_supported_by_refresh_status(self):
        appointment_id = self._appointment(self.patient_none)["id"]
        invoice = Invoice.objects.create(
            cabinet=self.cab1,
            appointment_id=appointment_id,
            amount=150.00,
            recipient=self.apiuser,
        )
        Payment.objects.create(
            invoice=invoice,
            amount=150.00,
            kind=Payment.Kind.PATIENT,
            method=Payment.Method.CASH,
            created_by=self.apiuser,
        )
        invoice.refresh_status()
        self.assertEqual(invoice.status, Invoice.Status.PAID)

    def test_pdf_is_generated(self):
        data = self._invoice(self.patient_cnops)
        response = self.client.get(f"/api/invoices/{data['id']}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_note_can_be_attached_to_payment(self):
        data = self._invoice(self.patient_cnops)
        response = self.client.post(
            f"/api/invoices/{data['id']}/payments/",
            {
                "amount": "10.00",
                "kind": "patient",
                "method": "cash",
                "note": "acompte",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["note"], "acompte")

    def test_assistant_who_is_not_admin_cannot_create_invoice_in_other_cabinet(self):
        sec_user, _ = self.factories.assistant("sec1", self.cab1)
        client = APIClient()
        client.force_authenticate(user=sec_user)
        foreign_patient = self.factories.patient(self.cab2, "ZZ000000")
        appointment = client.post(
            "/api/appointments/",
            {
                "patient": foreign_patient.id,
                "doctor": self.doctor.id,
                "start": to_iso(future_start(3)),
                "end": to_iso(future_start(4)),
                "reason": "Consultation",
            },
            format="json",
        )
        # assistant from Cab 1 cannot create an appointment for Cab 2's patient
        self.assertEqual(appointment.status_code, 400)


class InvoiceListFiltersTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        doc_user, self.doctor = self.factories.doctor("doc1", self.cab1)
        self.apiuser = doc_user
        self.client = APIClient()
        self.client.force_authenticate(user=self.apiuser)
        self.base = timezone.now()
        self._slot = 0

    def _create(self, patient, paid, amount):
        self._slot += 3
        start, end = make_start_end(future_start(self._slot))
        appointment = self.client.post(
            "/api/appointments/",
            {
                "patient": patient.id,
                "doctor": self.doctor.id,
                "start": to_iso(start),
                "end": to_iso(end),
                "reason": "Consultation",
            },
            format="json",
        ).data
        invoice = self.client.post(
            "/api/invoices/",
            {"appointment": appointment["id"], "amount": amount},
            format="json",
        ).data
        if paid:
            self.client.post(
                f"/api/invoices/{invoice['id']}/payments/",
                {"amount": amount, "kind": "patient", "method": "cash"},
                format="json",
            )
        return invoice

    def test_status_and_payed_filters(self):
        patient = self.factories.patient(self.cab1, "BE111111")
        paid = self._create(patient, True, "100.00")
        unpaid = self._create(patient, False, "200.00")
        by_status = self.client.get(
            "/api/invoices/", {"status": "paid"}
        ).data["results"]
        self.assertEqual({row["id"] for row in by_status}, {paid["id"]})
        by_payed = self.client.get(
            "/api/invoices/", {"payed": "true"}
        ).data["results"]
        self.assertEqual({row["id"] for row in by_payed}, {paid["id"]})

    def test_appointment_filter(self):
        patient = self.factories.patient(self.cab1, "BE222222")
        invoice = self._create(patient, False, "150.00")
        response = self.client.get(
            "/api/invoices/", {"appointment": invoice["appointment"]}
        )
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], invoice["id"])

    def test_date_range_filters(self):
        patient = self.factories.patient(self.cab1, "BE333333")
        old = self._create(patient, False, "90.00")
        Invoice.objects.filter(pk=old["id"]).update(
            date=self.base - timezone.timedelta(days=5)
        )
        recent = self._create(patient, False, "45.00")
        today = self.base.date().isoformat()
        response = self.client.get(
            "/api/invoices/",
            {"date_from": today, "date_to": today},
        )
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], recent["id"])

    def test_ordering_by_amount(self):
        patient = self.factories.patient(self.cab1, "BE444444")
        small = self._create(patient, False, "50.00")
        big = self._create(patient, False, "900.00")
        response = self.client.get("/api/invoices/", {"ordering": "amount"})
        amounts = [row["amount"] for row in response.data["results"]]
        self.assertEqual(amounts, ["50.00", "900.00"])
        self.assertEqual(response.data["results"][0]["id"], small["id"])

    def test_update_rebuilds_items_and_payed_override(self):
        patient = self.factories.patient(self.cab1, "BE555555")
        invoice = self._create(patient, False, "100.00")
        response = self.client.put(
            f"/api/invoices/{invoice['id']}/",
            {
                "appointment": invoice["appointment"],
                "amount": "120.00",
                "items": [
                    {"label": "Consultation", "amount": "120.00"},
                    {"label": "Soin", "amount": "0.00"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["items"]), 2)
        response = self.client.patch(
            f"/api/invoices/{invoice['id']}/", {"payed": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "paid")

    def test_admin_can_bill_any_cabinet(self):
        admin = self.factories.admin("boss")
        client = APIClient()
        client.force_authenticate(user=admin)
        cab2_patient = self.factories.patient(self.cab2, "ZZ000000")
        self._slot += 3
        start, end = make_start_end(future_start(self._slot))
        appointment = client.post(
            "/api/appointments/",
            {
                "cabinet": self.cab2.id,
                "patient": cab2_patient.id,
                "start": to_iso(start),
                "end": to_iso(end),
                "reason": "Consultation",
            },
            format="json",
        ).data
        response = client.post(
            "/api/invoices/",
            {"appointment": appointment["id"], "amount": "80.00"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab2.id)