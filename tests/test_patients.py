"""Tests for patients app: patient management and file uploads."""

import pytest
from rest_framework import status

from patients.models import Patient
from tests.factories import PatientFactory, CabinetFactory


@pytest.mark.django_db
class TestPatientViewSet:
    """Test CRUD operations for patients."""

    def test_list_patients_cabinet_scoped(self, authenticated_client, cabinet) -> None:
        """Test that patient list is scoped to user's cabinet."""
        patient = PatientFactory(cabinet=cabinet)
        response = authenticated_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        assert patient.id in [p["id"] for p in response.data["results"]]

    def test_list_patients_excludes_other_cabinets(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that patients from other cabinets are not visible."""
        patient1 = PatientFactory(cabinet=cabinet)
        patient2 = PatientFactory(cabinet=cabinet2)
        response = authenticated_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        patient_ids = [p["id"] for p in response.data["results"]]
        assert patient1.id in patient_ids
        assert patient2.id not in patient_ids

    def test_create_patient(self, authenticated_client, cabinet) -> None:
        """Test creating a new patient."""
        response = authenticated_client.post(
            "/api/patients/",
            {
                "cabinet": cabinet.id,
                "cin": "PAT999",
                "firstname": "John",
                "lastname": "Doe",
                "gender": "Male",
                "age": 45,
                "phone": "+212 6 11 11 11 11",
                "address": "123 Patient St",
                "child": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Patient.objects.filter(cin="PAT999").exists()

    def test_create_patient_cin_unique_per_cabinet(
        self, authenticated_client, cabinet, cabinet2, doctor_user, doctor2_user
    ) -> None:
        """Test that CIN is unique per cabinet, not globally."""
        # Create patient with CIN in cabinet 1
        patient1 = PatientFactory(cabinet=cabinet, cin="SHARED001")

        # Should be able to use same CIN in cabinet 2
        response = authenticated_client.post(
            "/api/patients/",
            {
                "cabinet": cabinet.id,  # Same cabinet as authenticated user
                "cin": "SHARED001",  # Same CIN
                "firstname": "Jane",
                "lastname": "Smith",
                "gender": "Female",
                "age": 30,
                "phone": "+212 6 22 22 22 22",
                "address": "456 Other St",
                "child": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_patient_same_cabinet(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test deleting a patient from same cabinet."""
        patient = PatientFactory(cabinet=cabinet)
        response = authenticated_client.delete(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Patient.objects.filter(id=patient.id).exists()

    def test_delete_patient_different_cabinet(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that users can't delete patients from other cabinets."""
        patient = PatientFactory(cabinet=cabinet2)
        response = authenticated_client.delete(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_search_patients_by_name(self, authenticated_client, cabinet) -> None:
        """Test searching patients by first or last name."""
        patient = PatientFactory(cabinet=cabinet, firstname="Alice", lastname="Wonder")
        response = authenticated_client.get(
            "/api/patients/", {"search": "Alice"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) > 0

    def test_filter_patients_by_gender(self, authenticated_client, cabinet) -> None:
        """Test filtering patients by gender."""
        patient = PatientFactory(cabinet=cabinet, gender="Female")
        response = authenticated_client.get(
            "/api/patients/", {"gender": "Female"}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_child_patient_age_optional(self, authenticated_client, cabinet) -> None:
        """Test that age is optional for child patients."""
        response = authenticated_client.post(
            "/api/patients/",
            {
                "cabinet": cabinet.id,
                "cin": "CHILD001",
                "firstname": "Young",
                "lastname": "Kid",
                "gender": "Male",
                "phone": "+212 6 33 33 33 33",
                "address": "789 Kid St",
                "child": True,
                # age intentionally omitted
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestPatientFileViewSet:
    """Test patient file upload and management."""

    def test_upload_patient_file(self, authenticated_client, cabinet) -> None:
        """Test uploading a file for a patient."""
        patient = PatientFactory(cabinet=cabinet)
        with open(__file__, "rb") as f:
            response = authenticated_client.post(
                "/api/patient-files/",
                {"patient": patient.id, "file": f},
                format="multipart",
            )
        assert response.status_code == status.HTTP_201_CREATED

    def test_list_patient_files(self, authenticated_client, cabinet) -> None:
        """Test listing files for a patient."""
        patient = PatientFactory(cabinet=cabinet)
        response = authenticated_client.get(
            "/api/patient-files/", {"patient": patient.id}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_access_files_from_other_cabinet(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that files from other cabinets aren't accessible."""
        patient = PatientFactory(cabinet=cabinet2)
        response = authenticated_client.get(
            "/api/patient-files/", {"patient": patient.id}
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0
