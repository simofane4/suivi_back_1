from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsAdmin, IsCabinetStaff
from common.tenancy import ROLE_ADMIN, ROLE_ASSISTANT, ROLE_DOCTOR, StaffCabinetMixin
from common.viewsets import CabinetScopedViewSet

from .models import Assistant, Doctor
from .serializers import (
    AssistantCreateSerializer,
    AssistantSerializer,
    AssistantUpdateSerializer,
    DoctorCreateSerializer,
    DoctorSerializer,
    DoctorUpdateSerializer,
    UserSummarySerializer,
)


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds the caller's role and cabinet to the access token so the frontend
    can route without a second round trip."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        if hasattr(user, "doctor"):
            token["role"] = ROLE_DOCTOR
            token["cabinet_id"] = user.doctor.cabinet_id
        elif hasattr(user, "assistant"):
            token["role"] = ROLE_ASSISTANT
            token["cabinet_id"] = user.assistant.cabinet_id
        else:
            token["role"] = ROLE_ADMIN
            token["cabinet_id"] = None

        token["name"] = user.username
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["email"] = user.email
        return token


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer


class MeView(StaffCabinetMixin, APIView):
    """The authenticated account, including its role and cabinet."""

    def get(self, request):
        return Response(UserSummarySerializer(request.user).data, status=status.HTTP_200_OK)


class DoctorViewSet(CabinetScopedViewSet):
    """Doctors of the caller's cabinet.

    Creating a doctor also creates its login. Only an admin may create, modify
    or delete staff, so writes are admin-gated; the queryset is cabinet-scoped
    so staff only ever read their own clinic.
    """

    queryset = Doctor.objects.select_related("user", "cabinet", "specialiste").all()
    serializer_class = DoctorSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("user__first_name", "user__last_name", "user__username", "inp", "phone")
    filterset_fields = ("cabinet", "specialiste", "gender")
    ordering_fields = ("created_at", "inp")

    def get_serializer_class(self):
        if self.action == "create":
            return DoctorCreateSerializer
        if self.action in {"update", "partial_update"}:
            return DoctorUpdateSerializer
        return DoctorSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsCabinetStaff()]

    def perform_create(self, serializer):
        # `cabinet` comes from the payload rather than the caller: an admin may
        # create staff for any clinic, and only an admin reaches this branch.
        serializer.save()


class AssistantViewSet(CabinetScopedViewSet):
    queryset = Assistant.objects.select_related("user", "cabinet").all()
    serializer_class = AssistantSerializer
    permission_classes = (IsCabinetStaff,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ("user__first_name", "user__last_name", "user__username", "cin", "phone")
    filterset_fields = ("cabinet", "gender")
    ordering_fields = ("created_at",)

    def get_serializer_class(self):
        if self.action == "create":
            return AssistantCreateSerializer
        if self.action in {"update", "partial_update"}:
            return AssistantUpdateSerializer
        return AssistantSerializer

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return [IsCabinetStaff()]

    def perform_create(self, serializer):
        serializer.save()


class UserViewSet(StaffCabinetMixin, viewsets.ReadOnlyModelViewSet):
    """Directory of auth accounts. Admin only."""

    queryset = User.objects.all()
    serializer_class = UserSummarySerializer
    permission_classes = (IsAdmin,)
    # `search_fields` was declared but no SearchFilter backend was registered,
    # so `?search=` was silently ignored and returned every row.
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ("username", "first_name", "last_name", "email")
    ordering_fields = ("id", "username", "first_name", "last_name", "email", "is_active")
