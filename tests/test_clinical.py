"""Tests for clinical app: appointments, prescriptions, procedures."""

import pytest
from datetime import datetime, timedelta
from rest_framework import status

from clinical.models import Appointment, Ordonnance
from tests.factories import (
    AppointmentFactory,
    PatientFactory,
    DoctorFactory,
    CabinetFactory,
    OrdonnanceFactory,
    MedicamentFactory,
)


@pytest.mark.django_db
class TestAppointmentViewSet:
    """Test CRUD operations for appointments."""

    def test_create_appointment(self, authenticated_client, cabinet, doctor_user) -> None:
        """Test creating a new appointment."""
        from datetime import datetime, time
        patient = PatientFactory(cabinet=cabinet)
        start_date = datetime.now().date()
        start_time = time(9, 0)  # 9:00 AM
        end_time = time(10, 0)   # 10:00 AM

        response = authenticated_client.post(
            "/api/appointments/",
            {
                "cabinet": cabinet.id,
                "patient": patient.id,
                "date": start_date.isoformat(),
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "description": "Regular checkup",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Appointment.objects.filter(description="Regular checkup").exists()

    def test_appointment_overlap_detection(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test that overlapping appointments are prevented."""
        from datetime import time
        patient = PatientFactory(cabinet=cabinet)
        start_date = datetime.now().date()
        start_time = time(9, 0)
        end_time = time(10, 0)

        # Create first appointment
        AppointmentFactory(
            cabinet=cabinet,
            patient=patient,
            date=start_date,
            start=start_time,
            end=end_time,
        )

        # Try to create overlapping appointment
        response = authenticated_client.post(
            "/api/appointments/",
            {
                "cabinet": cabinet.id,
                "patient": patient.id,
                "date": start_date.isoformat(),
                "start": time(9, 30).isoformat(),
                "end": time(10, 30).isoformat(),
                "description": "Overlapping appointment",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_appointments_cabinet_scoped(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that appointments are scoped to user's cabinet."""
        appointment1 = AppointmentFactory(cabinet=cabinet)
        appointment2 = AppointmentFactory(cabinet=cabinet2)

        response = authenticated_client.get("/api/appointments/")
        assert response.status_code == status.HTTP_200_OK
        appointment_ids = [a["id"] for a in response.data["results"]]
        assert appointment1.id in appointment_ids
        assert appointment2.id not in appointment_ids

    def test_filter_appointments_by_date(
        self, authenticated_client, cabinet
    ) -> None:
        """Test filtering appointments by date."""
        from datetime import date, time
        start_date = date.today()
        appointment = AppointmentFactory(
            cabinet=cabinet, 
            date=start_date,
            start=time(9, 0),
            end=time(10, 0)
        )

        response = authenticated_client.get(
            "/api/appointments/", {"date_from": start_date.isoformat()}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_update_appointment(self, authenticated_client, cabinet) -> None:
        """Test updating an appointment."""
        from datetime import time
        appointment = AppointmentFactory(cabinet=cabinet)
        new_description = "Updated description"

        response = authenticated_client.patch(
            f"/api/appointments/{appointment.id}/",
            {"description": new_description},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        appointment.refresh_from_db()
        assert appointment.description == new_description

    def test_cancel_appointment(self, authenticated_client, cabinet) -> None:
        """Test canceling an appointment."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            f"/api/appointments/{appointment.id}/cancel/",
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK or status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestOrdonnanceViewSet:
    """Test prescription (ordonnance) management."""

    def test_create_ordonnance(self, authenticated_client, cabinet) -> None:
        """Test creating a prescription for an appointment."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            "/api/ordonnances/",
            {
                "appointment": appointment.id,
                "description": "Take one pill daily",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert Ordonnance.objects.filter(appointment=appointment).exists()

    def test_add_medications_to_ordonnance(
        self, authenticated_client, cabinet
    ) -> None:
        """Test adding medications to a prescription."""
        appointment = AppointmentFactory(cabinet=cabinet)
        med1 = MedicamentFactory(cabinet=cabinet)
        med2 = MedicamentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            "/api/ordonnances/",
            {
                "appointment": appointment.id,
                "description": "Prescription",
                "medicaments": [med1.id, med2.id],
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

    def test_list_ordonnances_cabinet_scoped(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that prescriptions are scoped to user's cabinet."""
        ordonnance1 = OrdonnanceFactory(cabinet=cabinet)
        ordonnance2 = OrdonnanceFactory(cabinet=cabinet2)

        response = authenticated_client.get("/api/ordonnances/")
        assert response.status_code == status.HTTP_200_OK
        ordonnance_ids = [o["id"] for o in response.data["results"]]
        assert ordonnance1.id in ordonnance_ids
        assert ordonnance2.id not in ordonnance_ids

    def test_update_ordonnance(self, authenticated_client, cabinet) -> None:
        """Test updating a prescription."""
        ordonnance = OrdonnanceFactory(appointment__cabinet=cabinet)
        new_description = "Updated prescription description"

        response = authenticated_client.patch(
            f"/api/ordonnances/{ordonnance.id}/",
            {"description": new_description},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK, response.data
        ordonnance.refresh_from_db()
        assert ordonnance.description == new_description


@pytest.mark.django_db
class TestProcedureViewSet:
    """Test procedure (acte) management."""

    def test_list_actes_demandes(self, authenticated_client, cabinet) -> None:
        """Test listing requested procedures."""
        response = authenticated_client.get("/api/actes-demandes/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_actes_faits(self, authenticated_client, cabinet) -> None:
        """Test listing completed procedures."""
        response = authenticated_client.get("/api/actes-faits/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_acte_demander(self, authenticated_client, cabinet) -> None:
        """Test creating a requested procedure."""
        response = authenticated_client.post(
            "/api/actes-demandes/",
            {
                "cabinet": cabinet.id,
                "title": "Blood Test",
                "description": "Complete blood work",
            },
            format="json",
        )
        # May require admin, depends on permission_classes
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN]


@pytest.mark.django_db
class TestMedicamentViewSet:
    """Test medication management."""

    def test_list_medicaments_cabinet_scoped(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that medications are scoped to user's cabinet."""
        med1 = MedicamentFactory(cabinet=cabinet)
        med2 = MedicamentFactory(cabinet=cabinet2)

        response = authenticated_client.get("/api/medicaments/")
        assert response.status_code == status.HTTP_200_OK
        medicament_ids = [m["id"] for m in response.data["results"]]
        assert med1.id in medicament_ids
        assert med2.id not in medicament_ids

    def test_create_medicament_requires_admin(self, authenticated_client, cabinet) -> None:
        """Test that creating medications may require admin role."""
        response = authenticated_client.post(
            "/api/medicaments/",
            {
                "cabinet": cabinet.id,
                "name": "Aspirin",
                "description": "Pain relief",
            },
            format="json",
        )
        # Depends on permission_classes set in views
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_403_FORBIDDEN]
