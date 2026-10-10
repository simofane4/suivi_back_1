from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import ActeDemander, ActeFait, Medicament
from core.factories import Factories, future_start, make_start_end, to_iso


class PrescriptionTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.doc_user, self.doctor = self.factories.doctor("doc1", self.cab1)
        self.patient = self.factories.patient(self.cab1, "BE123456")
        self.med1 = Medicament.objects.create(
            cabinet=self.cab1,
            name="Paracetamol",
            name_fr="Paracétamol",
            name_ar="باراسيتامول",
            form="Comprimé",
            dosage="500 mg",
        )
        self.med2 = Medicament.objects.create(
            cabinet=self.cab1,
            name="Ibuprofen",
            name_fr="Ibuprofène",
            name_ar="إيبوبروفين",
            form="Comprimé",
            dosage="400 mg",
        )
        self.acte_fait = ActeFait.objects.create(cabinet=self.cab1, title="Consultation")
        self.acte_demander = ActeDemander.objects.create(
            cabinet=self.cab1, title="NFS"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def _appointment(self):
        start, end = make_start_end(future_start(5))
        return self.client.post(
            "/api/appointments/",
            {
                "patient": self.patient.id,
                "doctor": self.doctor.id,
                "start": to_iso(start),
                "end": to_iso(end),
                "reason": "Consultation",
            },
            format="json",
        ).data

    def payload(self, appointment_id, **overrides):
        data = {
            "appointment": appointment_id,
            "acte_demander": self.acte_demander.id,
            "acte_fait": self.acte_fait.id,
            "description": "Prendre matin et soir.",
            "medicaments": [
                {
                    "medicament": self.med1.id,
                    "dosage": "1 cp x2/j",
                    "duration": "5 jours",
                },
                {
                    "medicament": self.med2.id,
                    "dosage": "1 cp x3/j",
                    "duration": "3 jours",
                },
            ],
        }
        data.update(overrides)
        return data

    def test_create_bilingual_ordonnance_with_lines(self):
        appointment = self._appointment()
        response = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab1.id)
        self.assertEqual(len(response.data["medicaments_list"]), 2)
        names = {row["medicament_name"] for row in response.data["medicaments_list"]}
        self.assertEqual(names, {"Paracétamol", "Ibuprofène"})

    def test_medicaments_list_is_read_after_reload(self):
        appointment = self._appointment()
        created = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        ).data
        fresh = self.client.get(f"/api/ordonnances/{created['id']}/").data
        self.assertEqual(len(fresh["medicaments_list"]), 2)

    def test_update_rebuilds_lines(self):
        appointment = self._appointment()
        created = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        ).data
        response = self.client.patch(
            f"/api/ordonnances/{created['id']}/",
            {
                "medicaments": [
                    {"medicament": self.med1.id, "dosage": "1 cp x1/j", "duration": "7 j"}
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["medicaments_list"]), 1)

    def test_foreign_patient_ordonnance_rejected(self):
        other_cab = self.factories.cabinet("Cab 2")
        foreign_patient = self.factories.patient(other_cab, "ZZ000000")
        start, end = make_start_end(future_start(5))
        from appointments.models import Appointment

        appointment = Appointment.objects.create(
            cabinet=other_cab,
            patient=foreign_patient,
            doctor=None,
            start=start,
            end=end,
            reason="x",
        )
        response = self.client.post(
            "/api/ordonnances/",
            self.payload(appointment.id),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_pdf_is_generated(self):
        appointment = self._appointment()
        created = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        ).data
        response = self.client.get(f"/api/ordonnances/{created['id']}/pdf/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_list_filters_by_appointment_and_patient(self):
        appointment = self._appointment()
        created = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        ).data
        by_appointment = self.client.get(
            "/api/ordonnances/",
            {"appointment": appointment["id"]},
        ).data["results"]
        self.assertEqual(len(by_appointment), 1)
        by_patient = self.client.get(
            "/api/ordonnances/", {"patient": self.patient.id}
        ).data["results"]
        self.assertEqual({row["id"] for row in by_patient}, {created["id"]})

    def test_list_filters_by_medicament(self):
        appointment = self._appointment()
        created = self.client.post(
            "/api/ordonnances/", self.payload(appointment["id"]), format="json"
        ).data
        response = self.client.get(
            "/api/ordonnances/", {"medicament": self.med1.id}
        )
        rows = response.data["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], created["id"])


class PrescriptionAdminTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab2 = self.factories.cabinet("Cab 2")
        self.admin = self.factories.admin("boss")
        self.patient = self.factories.patient(self.cab2, "BE999999")
        self.med = Medicament.objects.create(
            cabinet=self.cab2, name="Med X", name_fr="Med X", name_ar="ميد"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_admin_can_create_ordonnance_for_any_cabinet(self):
        from appointments.models import Appointment
        from core.factories import future_start, make_start_end, to_iso

        start, end = make_start_end(future_start())
        appointment = Appointment.objects.create(
            cabinet=self.cab2,
            patient=self.patient,
            start=start,
            end=end,
            reason="Consultation",
        )
        response = self.client.post(
            "/api/ordonnances/",
            {
                "appointment": appointment.id,
                "medicaments": [
                    {"medicament": self.med.id, "dosage": "1 cp", "duration": "3 j"}
                ],
                "description": "Suivi",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab2.id)
        self.assertEqual(len(response.data["medicaments_list"]), 1)