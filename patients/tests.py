from django.test import TestCase
from rest_framework.test import APIClient

from core.factories import Factories


class PatientTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.doc_user, _ = self.factories.doctor("doc1", self.cab1)
        self.patient1 = self.factories.patient(
            self.cab1, "BE123456", firstname="Ahmed", lastname="Benali"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def payload(self, cin="BE999999", **overrides):
        data = {
            "cin": cin,
            "firstname": "Fatima",
            "lastname": "El Idrissi",
            "gender": "Female",
            "age": 30,
            "phone": "0612345678",
        }
        data.update(overrides)
        return data

    def test_create_patient_is_scoped_to_doctor_cabinet(self):
        response = self.client.post("/api/patients/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["cabinet"], self.cab1.id)
        self.assertEqual(response.data["cabinet_name"], self.cab1.name)

    def test_duplicate_cin_in_same_cabinet_rejected(self):
        response = self.client.post(
            "/api/patients/", self.payload(cin=self.patient1.cin), format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cin", str(response.data))

    def test_same_cin_allowed_in_another_cabinet(self):
        admin = self.factories.admin("boss")
        client = APIClient()
        client.force_authenticate(user=admin)
        response = client.post(
            "/api/patients/",
            self.payload(cin=self.patient1.cin, cabinet=self.cab2.id),
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_dossier_aggregates_medical_record(self):
        antecedent = self.patient1.antecedents.create(label="HTA")
        self.patient1.allergies.create(name="Pénicilline")
        self.patient1.observations.create(
            diagnostic="I10", diagnostic_label="HTA essentielle"
        )
        response = self.client.get(f"/api/patients/{self.patient1.id}/dossier/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patient"]["id"], self.patient1.id)
        self.assertEqual(len(response.data["antecedents"]), 1)
        self.assertEqual(response.data["antecedents"][0]["id"], antecedent.id)
        self.assertEqual(len(response.data["allergies"]), 1)
        self.assertEqual(len(response.data["observations"]), 1)

    def test_doctor_cannot_view_foreign_cabinet_dossier(self):
        other = self.factories.patient(self.cab2, "ZZ000000")
        response = self.client.get(f"/api/patients/{other.id}/dossier/")
        self.assertEqual(response.status_code, 404)

    def test_filters_by_lastname(self):
        response = self.client.get(
            "/api/patients/", {"lastname": "Benali"}
        )
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {self.patient1.id})

    def test_update_to_duplicate_cin_rejected(self):
        other = self.factories.patient(self.cab1, "BE888888", lastname="Autre")
        response = self.client.patch(
            f"/api/patients/{other.id}/",
            {"cin": self.patient1.cin},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cin", str(response.data))

    def test_update_keeps_cabinet_for_staff(self):
        response = self.client.patch(
            f"/api/patients/{self.patient1.id}/",
            {"lastname": "El Abdouli"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cabinet"], self.cab1.id)
        self.assertEqual(response.data["lastname"], "El Abdouli")

    def test_can_attach_a_patient_file(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        small = SimpleUploadedFile(
            "rapport.pdf", b"%PDF-1.4 tiny", content_type="application/pdf"
        )
        response = self.client.post(
            "/api/patient-files/",
            {"patient": self.patient1.id, "file": small},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["patient"], self.patient1.id)

    def test_oversized_patient_file_rejected(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        big = SimpleUploadedFile("big.pdf", b"x" * (5 * 1024 * 1024 + 1))
        response = self.client.post(
            "/api/patient-files/",
            {"patient": self.patient1.id, "file": big},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_cannot_attach_file_to_foreign_patient(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        foreign = self.factories.patient(self.cab2, "ZZ000000")
        file = SimpleUploadedFile("a.pdf", b"data")
        response = self.client.post(
            "/api/patient-files/",
            {"patient": foreign.id, "file": file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)