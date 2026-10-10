from drf_spectacular.utils import extend_schema
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from core.mixins import CabinetScopedQuerysetMixin
from core.permissions import (
    ADMIN,
    IsAdmin,
    IsCabinetStaffOrAdmin,
)

from .models import Assistant, Cabinet, Doctor, Specialite, User
from .serializers import (
    AssistantSerializer,
    CabinetSerializer,
    CustomTokenObtainPairSerializer,
    DoctorSerializer,
    SpecialiteSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    """`POST /api/auth/token/` — obtain access/refresh tokens."""

    serializer_class = CustomTokenObtainPairSerializer


class MeView(APIView):
    """`GET /api/auth/me/` — current user's profile, role and cabinet."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer})
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class CabinetViewSet(ModelViewSet):
    """`/api/cabinets/` — admin manages; staff only see their own."""

    queryset = Cabinet.objects.all()
    serializer_class = CabinetSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "number", "address"]
    ordering_fields = ["name", "created_at", "id"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser or getattr(user, "role", None) == ADMIN:
            return queryset
        return queryset.filter(id=user.cabinet_id)


class SpecialiteViewSet(ModelViewSet):
    """`/api/specialites/` — global catalogue, read for all, admin writes."""

    queryset = Specialite.objects.all()
    serializer_class = SpecialiteSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsAuthenticated()]
        return [IsAdmin()]


class DoctorViewSet(CabinetScopedQuerysetMixin, ModelViewSet):
    """`/api/doctors/` — staff can list, admins manage."""

    queryset = Doctor.objects.select_related("user", "cabinet", "specialiste")
    serializer_class = DoctorSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "inp",
        "phone",
    ]
    ordering_fields = ["id", "created_at", "user__first_name"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsCabinetStaffOrAdmin()]
        return [IsAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        for param, field in (
            ("cabinet", "cabinet_id"),
            ("specialiste", "specialiste_id"),
            ("gender", "gender"),
        ):
            value = params.get(param)
            if value not in (None, ""):
                queryset = queryset.filter(**{field: value})
        return queryset


class AssistantViewSet(CabinetScopedQuerysetMixin, ModelViewSet):
    """`/api/assistants/` — staff can list, admins manage."""

    queryset = Assistant.objects.select_related("user", "cabinet")
    serializer_class = AssistantSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "user__username",
        "user__first_name",
        "user__last_name",
        "cin",
        "phone",
    ]
    ordering_fields = ["id", "created_at", "user__first_name"]

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [IsCabinetStaffOrAdmin()]
        return [IsAdmin()]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        for param, field in (("cabinet", "cabinet_id"), ("gender", "gender")):
            value = params.get(param)
            if value not in (None, ""):
                queryset = queryset.filter(**{field: value})
        return queryset


class UserViewSet(ReadOnlyModelViewSet):
    """`/api/users/` — read-only directory, admins only."""

    queryset = User.objects.select_related("cabinet")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = [
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser or getattr(user, "role", None) == ADMIN:
            return queryset
        return queryset.filter(cabinet_id=user.cabinet_id)
