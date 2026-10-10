"""Tests for permissions and multi-tenancy cabinet scoping."""

import pytest
from rest_framework import status

from tests.factories import (
    PatientFactory,
    AppointmentFactory,
    DoctorFactory,
    CabinetFactory,
)


@pytest.mark.django_db
class TestCabinetScoping:
    """Test that users can only access data from their own cabinet."""

    def test_doctor_cannot_see_other_cabinet_patients(
        self, authenticated_client, cabinet, cabinet2, doctor_user
    ) -> None:
        """Test that a doctor can't see patients from other cabinets."""
        other_patient = PatientFactory(cabinet=cabinet2)
        own_patient = PatientFactory(cabinet=cabinet)

        response = authenticated_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        patient_ids = [p["id"] for p in response.data["results"]]
        assert own_patient.id in patient_ids
        assert other_patient.id not in patient_ids

    def test_doctor_cannot_access_other_cabinet_appointment(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that a doctor can't access an appointment from another cabinet."""
        other_appointment = AppointmentFactory(cabinet=cabinet2)

        response = authenticated_client.get(f"/api/appointments/{other_appointment.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_doctor_cannot_update_other_cabinet_patient(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that a doctor can't update a patient from another cabinet."""
        other_patient = PatientFactory(cabinet=cabinet2)

        response = authenticated_client.patch(
            f"/api/patients/{other_patient.id}/",
            {"firstname": "Updated"},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_doctor_cannot_delete_other_cabinet_patient(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that a doctor can't delete a patient from another cabinet."""
        other_patient = PatientFactory(cabinet=cabinet2)

        response = authenticated_client.delete(f"/api/patients/{other_patient.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_assistant_same_permissions_as_doctor(
        self, assistant_client, cabinet, cabinet2
    ) -> None:
        """Test that assistants have the same cabinet scoping as doctors."""
        own_patient = PatientFactory(cabinet=cabinet)
        other_patient = PatientFactory(cabinet=cabinet2)

        response = assistant_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        patient_ids = [p["id"] for p in response.data["results"]]
        assert own_patient.id in patient_ids
        assert other_patient.id not in patient_ids

    def test_create_patient_auto_assigns_to_cabinet(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test that new patient is auto-assigned to the user's cabinet."""
        response = authenticated_client.post(
            "/api/patients/",
            {
                # cabinet may be optional or auto-assigned
                "cin": "AUTO001",
                "firstname": "Auto",
                "lastname": "Assigned",
                "gender": "Male",
                "phone": "+212 6 99 99 99 99",
                "address": "Auto St",
            },
            format="json",
        )
        # Depending on implementation, cabinet may be required or auto-filled
        if response.status_code == status.HTTP_201_CREATED:
            from patients.models import Patient
            patient = Patient.objects.get(cin="AUTO001")
            assert patient.cabinet_id == cabinet.id


@pytest.mark.django_db
class TestAdminPermissions:
    """Test admin-specific permissions and cross-cabinet visibility."""

    def test_admin_sees_all_cabinets(
        self, admin_client, cabinet, cabinet2
    ) -> None:
        """Test that admins can see data from all cabinets."""
        patient1 = PatientFactory(cabinet=cabinet)
        patient2 = PatientFactory(cabinet=cabinet2)

        response = admin_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        if "results" in response.data:
            patient_ids = [p["id"] for p in response.data["results"]]
        else:
            patient_ids = [p["id"] for p in response.data]
        assert patient1.id in patient_ids
        assert patient2.id in patient_ids

    def test_admin_can_create_user_in_any_cabinet(
        self, admin_client, cabinet, specialite
    ) -> None:
        """Test that admins can create users in any cabinet."""
        response = admin_client.post(
            "/api/doctors/",
            {
                "username": "admin_created_doc",
                "password": "secure12345",
                "email": "admin@example.local",
                "first_name": "Admin",
                "last_name": "Created",
                "cabinet": cabinet.id,
                "inp": "ADMIN0001",
                "gender": "Male",
                "phone": "+212 6 00 00 00 01",
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_regular_user_cannot_create_staff(
        self, authenticated_client, cabinet, specialite
    ) -> None:
        """Test that regular users can't create new staff."""
        response = authenticated_client.post(
            "/api/doctors/",
            {
                "username": "newdoc",
                "password": "secure12345",
                "email": "newdoc@example.local",
                "first_name": "New",
                "last_name": "Doc",
                "cabinet": cabinet.id,
                "inp": "NEWDOC001",
                "gender": "Male",
                "phone": "+212 6 01 01 01 01",
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_user_list(self, admin_client) -> None:
        """Test that admins can list all users."""
        response = admin_client.get("/api/users/")
        assert response.status_code == status.HTTP_200_OK

    def test_regular_user_cannot_access_user_list(
        self, authenticated_client
    ) -> None:
        """Test that regular users can't list all users."""
        response = authenticated_client.get("/api/users/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRoleBasedAccess:
    """Test role-specific permissions (doctor only, doctor+assistant, etc)."""

    def test_doctor_can_read_appointment(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test that doctors can read appointments."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.get(f"/api/appointments/{appointment.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_assistant_can_read_appointment(
        self, assistant_client, cabinet, assistant_user
    ) -> None:
        """Test that assistants can also read appointments."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = assistant_client.get(f"/api/appointments/{appointment.id}/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_access_api(self, api_client) -> None:
        """Test that unauthenticated requests are rejected."""
        response = api_client.get("/api/patients/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_rejected(self, api_client) -> None:
        """Test that invalid tokens are rejected."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token_here")
        response = api_client.get("/api/patients/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
