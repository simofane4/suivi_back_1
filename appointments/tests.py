from datetime import datetime, timedelta, time as dtime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from core.factories import (
    Factories,
    future_start,
    make_start_end,
    to_iso,
)


class AppointmentTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.doc_user, self.doctor = self.factories.doctor("doc1", self.cab1)
        self.patient = self.factories.patient(self.cab1, "BE123456")
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def payload(self, start=None, **overrides):
        start = start or future_start()
        start, end = make_start_end(start)
        data = {
            "patient": self.patient.id,
            "doctor": self.doctor.id,
            "start": to_iso(start),
            "end": to_iso(end),
            "reason": "Consultation",
        }
        data.update(overrides)
        return data

    def test_create_appointment(self):
        response = self.client.post(
            "/api/appointments/", self.payload(), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab1.id)
        self.assertEqual(response.data["patient_name"], "Ahmed Benali")

    def test_overlapping_appointment_rejected(self):
        start = future_start()
        first = self.client.post(
            "/api/appointments/", self.payload(start), format="json"
        )
        self.assertEqual(first.status_code, 201)
        overlap = self.client.post(
            "/api/appointments/",
            self.payload(start + timedelta(minutes=30)),
            format="json",
        )
        self.assertEqual(overlap.status_code, 400)

    def test_past_appointment_rejected(self):
        past = timezone.now() - timezone.timedelta(hours=1)
        response = self.client.post(
            "/api/appointments/", self.payload(past), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("start", str(response.data))

    def test_cancelled_appointment_does_not_block_slot(self):
        start = future_start()
        first = self.client.post(
            "/api/appointments/", self.payload(start), format="json"
        )
        self.assertEqual(first.status_code, 201)
        self.client.patch(
            f"/api/appointments/{first.data['id']}/",
            {"status": "cancelled"},
            format="json",
        )
        second = self.client.post(
            "/api/appointments/", self.payload(start), format="json"
        )
        self.assertEqual(second.status_code, 201)

    def test_agenda_returns_only_requested_day(self):
        today = timezone.localdate()
        start = timezone.make_aware(datetime.combine(today, dtime(10, 0)))
        appointment = Appointment.objects.create(
            cabinet=self.cab1,
            patient=self.patient,
            doctor=self.doctor,
            start=start,
            end=start + timedelta(hours=1),
            reason="Consultation",
        )
        response = self.client.get(
            "/api/appointments/agenda/",
            {"date": today.isoformat(), "praticien": self.doctor.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["id"], appointment.id)

    def test_status_filter(self):
        start, end = make_start_end(future_start())
        Appointment.objects.create(
            cabinet=self.cab1,
            patient=self.patient,
            doctor=self.doctor,
            start=start,
            end=end,
            status=Appointment.Status.CONFIRMED,
            reason="Suivi",
        )
        response = self.client.get(
            "/api/appointments/", {"status": "confirmed"}
        )
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "confirmed")

    def test_date_from_date_to_filters(self):
        Appointment.objects.create(
            cabinet=self.cab1,
            patient=self.patient,
            doctor=self.doctor,
            start=timezone.make_aware(
                datetime.combine(timezone.localdate(), dtime(10))
            ),
            end=timezone.make_aware(
                datetime.combine(timezone.localdate(), dtime(11))
            ),
            status=Appointment.Status.SCHEDULED,
            reason="Aujourd'hui",
        )
        tomorrow = timezone.localdate() + timedelta(days=1)
        Appointment.objects.create(
            cabinet=self.cab1,
            patient=self.patient,
            doctor=self.doctor,
            start=timezone.make_aware(datetime.combine(tomorrow, dtime(10))),
            end=timezone.make_aware(datetime.combine(tomorrow, dtime(11))),
            status=Appointment.Status.SCHEDULED,
            reason="Demain",
        )
        today = timezone.localdate().isoformat()
        response = self.client.get(
            "/api/appointments/",
            {"date_from": today, "date_to": today},
        )
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reason"], "Aujourd'hui")

    def test_payed_filter(self):
        start, end = make_start_end(future_start())
        Appointment.objects.create(
            cabinet=self.cab1,
            patient=self.patient,
            doctor=self.doctor,
            start=start,
            end=end,
            status=Appointment.Status.COMPLETED,
            payed=True,
            reason="Payé",
        )
        response = self.client.get("/api/appointments/", {"payed": "true"})
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)

    def test_ordering_by_start(self):
        for delta in (1, 3, 2):
            Appointment.objects.create(
                cabinet=self.cab1,
                patient=self.patient,
                doctor=self.doctor,
                start=future_start(delta),
                end=future_start(delta) + timedelta(hours=1),
                reason=str(delta),
            )
        response = self.client.get(
            "/api/appointments/", {"ordering": "start"}
        )
        reasons = [row["reason"] for row in response.data["results"]]
        self.assertEqual(reasons, ["1", "2", "3"])

    def test_patch_moves_slot_and_keeps_cabinet(self):
        start, end = make_start_end(future_start())
        created = self.client.post(
            "/api/appointments/", self.payload(start), format="json"
        ).data
        new_start = future_start(6)
        response = self.client.patch(
            f"/api/appointments/{created['id']}/",
            {
                "start": to_iso(new_start),
                "end": to_iso(new_start + timedelta(hours=1)),
                "status": "confirmed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cabinet"], self.cab1.id)
        self.assertEqual(response.data["status"], "confirmed")

    def test_patching_same_slot_does_not_self_overlap(self):
        start = future_start()
        created = self.client.post(
            "/api/appointments/", self.payload(start), format="json"
        ).data
        response = self.client.patch(
            f"/api/appointments/{created['id']}/",
            {
                "start": to_iso(start),
                "end": to_iso(start + timedelta(hours=1)),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)


class AdminAppointmentTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.admin_user = self.factories.admin("boss")
        self.patient = self.factories.patient(self.cab2, "BE999999")
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_admin_can_create_cross_cabinet_appointment(self):
        response = self.client.post(
            "/api/appointments/",
            {
                "cabinet": self.cab2.id,
                "patient": self.patient.id,
                "start": to_iso(future_start(8)),
                "end": to_iso(future_start(9)),
                "reason": "Consultation",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab2.id)