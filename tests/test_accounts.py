"""Tests for accounts app: authentication, doctors, assistants."""

import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Doctor, Assistant
from cabinets.models import Cabinet
from tests.factories import DoctorFactory, AssistantFactory, SpecialiteFactory, CabinetFactory


@pytest.mark.django_db
class TestAuthentication:
    """Test JWT authentication endpoints."""

    def test_token_obtain_pair(self, api_client: APIClient, doctor_user: User) -> None:
        """Test obtaining a JWT token pair."""
        response = api_client.post(
            "/api/auth/token/",
            {"username": "doctor1", "password": "doctor12345"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_token_obtain_with_invalid_credentials(self, api_client: APIClient) -> None:
        """Test token obtain with invalid credentials."""
        response = api_client.post(
            "/api/auth/token/",
            {"username": "invalid", "password": "invalid"},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_contains_role_and_cabinet(
        self, api_client: APIClient, doctor_user: User
    ) -> None:
        """Test that token includes role and cabinet_id."""
        response = api_client.post(
            "/api/auth/token/",
            {"username": "doctor1", "password": "doctor12345"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        # Decode token to check claims
        import base64
        import json
        token = response.data["access"]
        # JWT format: header.payload.signature
        parts = token.split(".")
        # Add padding if necessary
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload))
        assert decoded["role"] == "doctor"
        assert "cabinet_id" in decoded

    def test_token_refresh(self, api_client: APIClient, doctor_user: User) -> None:
        """Test refreshing a JWT token."""
        # Obtain tokens
        response = api_client.post(
            "/api/auth/token/",
            {"username": "doctor1", "password": "doctor12345"},
            format="json",
        )
        refresh_token = response.data["refresh"]

        # Refresh
        response = api_client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_token_verify(self, api_client: APIClient, doctor_user: User) -> None:
        """Test verifying a JWT token."""
        # Obtain token
        response = api_client.post(
            "/api/auth/token/",
            {"username": "doctor1", "password": "doctor12345"},
            format="json",
        )
        access_token = response.data["access"]

        # Verify
        response = api_client.post(
            "/api/auth/token/verify/",
            {"token": access_token},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMeEndpoint:
    """Test the /api/auth/me/ endpoint for current user info."""

    def test_me_doctor(self, authenticated_client: APIClient, doctor_user: User) -> None:
        """Test getting current user info for a doctor."""
        response = authenticated_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "doctor1"
        assert response.data["role"] == "doctor"
        assert response.data["cabinet_id"] is not None

    def test_me_admin(self, admin_client: APIClient, admin_user: User) -> None:
        """Test getting current user info for an admin."""
        response = admin_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "admin"
        assert response.data["role"] == "admin"
        assert response.data["cabinet_id"] is None

    def test_me_assistant(self, assistant_client: APIClient, assistant_user: User) -> None:
        """Test getting current user info for an assistant."""
        response = assistant_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "assistant1"
        assert response.data["role"] == "assistant"
        assert response.data["cabinet_id"] is not None

    def test_me_unauthenticated(self, api_client: APIClient) -> None:
        """Test accessing me endpoint without authentication."""
        response = api_client.get("/api/auth/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestDoctorViewSet:
    """Test CRUD operations for doctors."""

    def test_list_doctors_cabinet_scoped(
        self, authenticated_client: APIClient, cabinet
    ) -> None:
        """Test that doctors list is scoped to user's cabinet."""
        # Create a doctor in the same cabinet
        doctor = DoctorFactory(cabinet=cabinet)
        response = authenticated_client.get("/api/doctors/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) > 0

    def test_create_doctor_requires_admin(self, authenticated_client: APIClient) -> None:
        """Test that only admins can create doctors."""
        cabinet = CabinetFactory()
        specialite = SpecialiteFactory()
        response = authenticated_client.post(
            "/api/doctors/",
            {
                "username": "newdoc",
                "password": "secure12345",
                "email": "newdoc@test.local",
                "first_name": "New",
                "last_name": "Doctor",
                "cabinet": cabinet.id,
                "inp": "DR00999",
                "gender": "Male",
                "phone": "+212 6 00 00 00 00",
                "specialiste": specialite.id,
            },
            format="json",
        )
        # Doctor (non-admin staff) can't create other doctors
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_doctor_as_admin(
        self, admin_client: APIClient, cabinet: Cabinet, specialite
    ) -> None:
        """Test that admins can create doctors."""
        response = admin_client.post(
            "/api/doctors/",
            {
                "username": "newdoc",
                "password": "secure12345",
                "email": "newdoc@test.local",
                "first_name": "New",
                "last_name": "Doctor",
                "cabinet": cabinet.id,
                "inp": "DR00999",
                "gender": "Male",
                "phone": "+212 6 00 00 00 00",
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Doctor.objects.filter(inp="DR00999").exists()
        # Check that user was created
        assert User.objects.filter(username="newdoc").exists()

    def test_update_doctor_as_admin(
        self, admin_client: APIClient, doctor_user: User
    ) -> None:
        """Test updating a doctor's info."""
        doctor = Doctor.objects.get(user=doctor_user)
        response = admin_client.patch(
            f"/api/doctors/{doctor.id}/",
            {
                "email": "newemail@test.local",
                "phone": "+212 6 11 11 11 11",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        doctor.refresh_from_db()
        assert doctor.user.email == "newemail@test.local"
        assert doctor.phone == "+212 6 11 11 11 11"

    def test_delete_doctor_requires_admin(
        self, authenticated_client: APIClient, doctor_user: User
    ) -> None:
        """Test that non-admins can't delete doctors."""
        doctor = Doctor.objects.get(user=doctor_user)
        response = authenticated_client.delete(f"/api/doctors/{doctor.id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAssistantViewSet:
    """Test CRUD operations for assistants."""

    def test_list_assistants_cabinet_scoped(
        self, authenticated_client: APIClient, cabinet
    ) -> None:
        """Test that assistants list is scoped to user's cabinet."""
        assistant = AssistantFactory(cabinet=cabinet)
        response = authenticated_client.get("/api/assistants/")
        assert response.status_code == status.HTTP_200_OK

    def test_create_assistant_as_admin(
        self, admin_client: APIClient, cabinet: Cabinet
    ) -> None:
        """Test creating an assistant as admin."""
        response = admin_client.post(
            "/api/assistants/",
            {
                "username": "newassist",
                "password": "secure12345",
                "email": "newassist@test.local",
                "first_name": "New",
                "last_name": "Assistant",
                "cabinet": cabinet.id,
                "gender": "Female",
                "phone": "+212 6 22 22 22 22",
                "cin": "CIN00999",
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Assistant.objects.filter(cin="CIN00999").exists()

    def test_update_assistant(
        self, admin_client: APIClient, assistant_user: User
    ) -> None:
        """Test updating an assistant's info."""
        assistant = Assistant.objects.get(user=assistant_user)
        response = admin_client.patch(
            f"/api/assistants/{assistant.id}/",
            {"phone": "+212 6 33 33 33 33"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assistant.refresh_from_db()
        assert assistant.phone == "+212 6 33 33 33 33"


@pytest.mark.django_db
class TestDoctorValidation:
    """Test doctor creation validation and constraints."""

    def test_unique_inp_constraint(
        self, admin_client: APIClient, cabinet: Cabinet, specialite, doctor_user: User
    ) -> None:
        """Test that doctor INP must be unique."""
        doctor = Doctor.objects.get(user=doctor_user)
        response = admin_client.post(
            "/api/doctors/",
            {
                "username": "doc2",
                "password": "secure12345",
                "email": "doc2@test.local",
                "first_name": "Doc",
                "last_name": "Two",
                "cabinet": cabinet.id,
                "inp": doctor.inp,  # Reuse existing INP
                "gender": "Male",
                "phone": "+212 6 44 44 44 44",
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unique_phone_constraint(
        self, admin_client: APIClient, cabinet: Cabinet, specialite, doctor_user: User
    ) -> None:
        """Test that doctor phone must be unique."""
        doctor = Doctor.objects.get(user=doctor_user)
        response = admin_client.post(
            "/api/doctors/",
            {
                "username": "doc3",
                "password": "secure12345",
                "email": "doc3@test.local",
                "first_name": "Doc",
                "last_name": "Three",
                "cabinet": cabinet.id,
                "inp": "DR01000",
                "gender": "Male",
                "phone": doctor.phone,  # Reuse existing phone
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_email_case_insensitive(
        self, admin_client: APIClient, cabinet: Cabinet, specialite, doctor_user: User
    ) -> None:
        """Test that email validation is case-insensitive."""
        doctor = Doctor.objects.get(user=doctor_user)
        response = admin_client.post(
            "/api/doctors/",
            {
                "username": "doc4",
                "password": "secure12345",
                "email": doctor.user.email.upper(),  # Use uppercase version
                "first_name": "Doc",
                "last_name": "Four",
                "cabinet": cabinet.id,
                "inp": "DR01001",
                "gender": "Male",
                "phone": "+212 6 55 55 55 55",
                "specialiste": specialite.id,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
