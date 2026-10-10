from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Specialite, User
from core.factories import Factories

URL_TOKEN = "/api/auth/token/"
URL_REFRESH = "/api/auth/token/refresh/"
URL_ME = "/api/auth/me/"


class AuthenticationTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cabinet = self.factories.cabinet("Clinique A")
        self.doctor_user, _ = self.factories.doctor("doc1", self.cabinet)
        self.client = APIClient()

    def test_login_returns_access_and_refresh(self):
        response = self.client.post(
            URL_TOKEN,
            {"username": "doc1", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_rejects_wrong_password(self):
        response = self.client.post(
            URL_TOKEN,
            {"username": "doc1", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_issues_a_new_access_token(self):
        login = self.client.post(
            URL_TOKEN,
            {"username": "doc1", "password": "password123"},
            format="json",
        )
        refresh = login.data["refresh"]
        response = self.client.post(
            URL_REFRESH, {"refresh": refresh}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get(URL_ME).status_code, 401)

    def test_me_with_bearer_token(self):
        login = self.client.post(
            URL_TOKEN,
            {"username": "doc1", "password": "password123"},
            format="json",
        )
        access = login.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(URL_ME)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "doc1")
        self.assertEqual(response.data["role"], User.Role.DOCTOR)
        self.assertEqual(response.data["cabinet_id"], self.cabinet.id)


class PermissionTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.patient1 = self.factories.patient(self.cab1, "P1")
        self.patient2 = self.factories.patient(self.cab2, "P2")
        self.tok = self.factories

    def _client_as(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_doctor_sees_only_his_cabinet_patients(self):
        doc1_user, _ = self.tok.doctor("docA", self.cab1)
        client = self._client_as(doc1_user)
        response = client.get("/api/patients/")
        self.assertEqual(response.status_code, 200)
        ids = {row["id"] for row in response.data["results"]}
        self.assertIn(self.patient1.id, ids)
        self.assertNotIn(self.patient2.id, ids)

    def test_doctor_cannot_retrieve_foreign_cabinet_patient(self):
        doc1_user, _ = self.tok.doctor("docB", self.cab1)
        client = self._client_as(doc1_user)
        response = client.get(f"/api/patients/{self.patient2.id}/")
        self.assertEqual(response.status_code, 404)

    def test_admin_sees_all_cabinets(self):
        admin_user = self.tok.admin("boss")
        client = self._client_as(admin_user)
        response = client.get("/api/patients/")
        ids = {row["id"] for row in response.data["results"]}
        self.assertIn(self.patient1.id, ids)
        self.assertIn(self.patient2.id, ids)

    def test_unauthenticated_gets_401_on_protected_route(self):
        client = APIClient()
        self.assertEqual(client.get("/api/patients/").status_code, 401)

    def test_cabinet_listing_scoped_for_staff(self):
        doc_user, _ = self.tok.doctor("docC", self.cab1)
        client = self._client_as(doc_user)
        response = client.get("/api/cabinets/")
        names = {row["name"] for row in response.data["results"]}
        self.assertEqual(names, {"Cab 1"})

    def test_assistant_cannot_manage_doctors(self):
        assistant_user, _ = self.tok.assistant("sec", self.cab1)
        client = self._client_as(assistant_user)
        response = client.post(
            "/api/doctors/", {"user": 1}, format="json"
        )
        self.assertEqual(response.status_code, 403)


class DoctorManagementTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.cab2 = self.factories.cabinet("Cab 2")
        self.spec, _ = Specialite.objects.get_or_create(name="Cardiologie")
        self.admin_user = self.factories.admin("boss")
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

    def test_admin_creates_doctor_with_credentials(self):
        response = self.client.post(
            "/api/doctors/",
            {
                "username": "docnew",
                "password": "password123",
                "first_name": "Karim",
                "last_name": "Tazi",
                "cabinet": self.cab1.id,
                "inp": "INP90909",
                "gender": "Male",
                "specialiste": self.spec.id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["user"]["username"], "docnew")
        self.assertEqual(response.data["cabinet_name"], self.cab1.name)
        self.assertTrue(
            User.objects.filter(username="docnew").exists()
        )

    def test_duplicate_username_rejected(self):
        self.factories.doctor("docA", self.cab1)
        response = self.client.post(
            "/api/doctors/",
            {
                "username": "docA",
                "password": "x",
                "cabinet": self.cab1.id,
                "inp": "INP1",
                "gender": "Male",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("username", str(response.data["error"]["fields"]))

    def test_admin_updates_doctor_username_and_cabinet(self):
        doc_user, doctor = self.factories.doctor("docB", self.cab1)
        response = self.client.patch(
            f"/api/doctors/{doctor.id}/",
            {
                "username": "docRenamed",
                "cabinet": self.cab2.id,
                "first_name": "Nouveau",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "docRenamed")
        doc_user.refresh_from_db()
        self.assertEqual(doc_user.cabinet_id, self.cab2.id)

    def test_admin_deletes_doctor(self):
        _, doctor = self.factories.doctor("docC", self.cab1)
        response = self.client.delete(f"/api/doctors/{doctor.id}/")
        self.assertEqual(response.status_code, 204)


class AdminOnlyRoutesTests(TestCase):
    def setUp(self):
        self.factories = Factories()
        self.cab1 = self.factories.cabinet("Cab 1")
        self.doc_user, _ = self.factories.doctor("doc1", self.cab1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.doc_user)

    def test_doctor_cannot_create_cabinet(self):
        response = self.client.post(
            "/api/cabinets/",
            {"name": "Cabinet pirate", "number": "CAB-X"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_doctor_cannot_create_specialite(self):
        response = self.client.post(
            "/api/specialites/", {"name": "Piratologie"}, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_doctor_can_list_specialites(self):
        response = self.client.get("/api/specialites/")
        self.assertEqual(response.status_code, 200)

    def test_doctor_sees_only_his_cabinet_doctors(self):
        self.factories.doctor("docA", self.cab1)
        self.factories.doctor("docB", self.factories.cabinet("Cab 2"))
        response = self.client.get("/api/doctors/")
        doctors = response.data["results"]
        self.assertTrue(all(row["cabinet"] == self.cab1.id for row in doctors))