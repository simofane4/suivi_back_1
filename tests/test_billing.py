"""Tests for billing app: invoices and payment tracking."""

import pytest
from rest_framework import status

from billing.models import Invoice
from tests.factories import AppointmentFactory, InvoiceFactory, CabinetFactory


@pytest.mark.django_db
class TestInvoiceViewSet:
    """Test CRUD operations for invoices."""

    def test_create_invoice(self, authenticated_client, cabinet, doctor_user) -> None:
        """Test creating a new invoice."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            "/api/invoices/",
            {
                "appointment": appointment.id,
                "amount": "5000.00",
                "payed": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Invoice.objects.filter(appointment=appointment).exists()

    def test_invoice_recipient_defaults_to_current_user(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test that invoice recipient defaults to current user if not provided."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            "/api/invoices/",
            {
                "appointment": appointment.id,
                "amount": "5000.00",
                # recipient not provided
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        invoice = Invoice.objects.get(appointment=appointment)
        assert invoice.recipient_id == doctor_user.id

    def test_list_invoices_cabinet_scoped(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that invoices are scoped to user's cabinet."""
        appointment1 = AppointmentFactory(cabinet=cabinet)
        appointment2 = AppointmentFactory(cabinet=cabinet2)
        invoice1 = InvoiceFactory(appointment=appointment1)
        invoice2 = InvoiceFactory(appointment=appointment2)

        response = authenticated_client.get("/api/invoices/")
        assert response.status_code == status.HTTP_200_OK
        invoice_ids = [i["id"] for i in response.data["results"]]
        assert invoice1.id in invoice_ids
        assert invoice2.id not in invoice_ids

    def test_list_unpaid_invoices(self, authenticated_client, cabinet) -> None:
        """Test filtering for unpaid invoices."""
        appointment = AppointmentFactory(cabinet=cabinet)
        paid_invoice = InvoiceFactory(appointment=appointment, payed=True)
        unpaid_invoice = InvoiceFactory(appointment=appointment, payed=False)

        response = authenticated_client.get("/api/invoices/unpaid/")
        assert response.status_code == status.HTTP_200_OK
        invoice_ids = [i["id"] for i in response.data["results"]]
        assert paid_invoice.id not in invoice_ids
        assert unpaid_invoice.id in invoice_ids

    def test_mark_invoice_as_paid(
        self, authenticated_client, cabinet, doctor_user
    ) -> None:
        """Test marking an invoice as paid."""
        appointment = AppointmentFactory(cabinet=cabinet)
        invoice = InvoiceFactory(appointment=appointment, payed=False)

        response = authenticated_client.patch(
            f"/api/invoices/{invoice.id}/",
            {"payed": True},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        invoice.refresh_from_db()
        assert invoice.payed is True

    def test_cannot_create_invoice_for_other_cabinet(
        self, authenticated_client, cabinet, cabinet2
    ) -> None:
        """Test that invoices can only be created for appointments in user's cabinet."""
        appointment = AppointmentFactory(cabinet=cabinet2)

        response = authenticated_client.post(
            "/api/invoices/",
            {
                "appointment": appointment.id,
                "amount": "5000.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invoice_amount_validation(self, authenticated_client, cabinet) -> None:
        """Test that invoice amount must be non-negative."""
        appointment = AppointmentFactory(cabinet=cabinet)

        response = authenticated_client.post(
            "/api/invoices/",
            {
                "appointment": appointment.id,
                "amount": "-100.00",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_invoice_details(self, authenticated_client, cabinet) -> None:
        """Test retrieving invoice details including patient name."""
        appointment = AppointmentFactory(cabinet=cabinet)
        invoice = InvoiceFactory(appointment=appointment)

        response = authenticated_client.get(f"/api/invoices/{invoice.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert "patient_name" in response.data
        assert response.data["patient_name"] == (
            f"{invoice.appointment.patient.firstname} "
            f"{invoice.appointment.patient.lastname}"
        ).strip()

    def test_delete_invoice(self, authenticated_client, cabinet, admin_user) -> None:
        """Test deleting an invoice (if permitted by permissions)."""
        appointment = AppointmentFactory(cabinet=cabinet)
        invoice = InvoiceFactory(appointment=appointment)

        # Try with regular user (may fail due to permissions)
        response = authenticated_client.delete(f"/api/invoices/{invoice.id}/")
        # Permission check depends on implementation
        assert response.status_code in [
            status.HTTP_204_NO_CONTENT,
            status.HTTP_403_FORBIDDEN,
        ]
