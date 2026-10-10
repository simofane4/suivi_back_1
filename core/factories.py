from collections.abc import Callable

from django.utils import timezone

from accounts.models import Assistant, Cabinet, Doctor, Specialite, User
from patients.models import Patient


class Factories:
    """Small object factory used across every test module."""

    def __init__(self):
        self._cabinet_numbers = 0

    def cabinet(self, name: str | None = None) -> Cabinet:
        self._cabinet_numbers += 1
        return Cabinet.objects.create(
            name=name or f"Cabinet {self._cabinet_numbers}",
            number=f"CAB-{self._cabinet_numbers:04d}",
            address="Casablanca",
        )

    def user(
        self,
        username: str,
        *,
        role: str,
        cabinet: Cabinet | None = None,
        password: str = "password123",
    ) -> User:
        user = User.objects.create_user(username=username, password=password)
        user.role = role
        user.cabinet = cabinet
        user.save(update_fields=["role", "cabinet"])
        return user

    def admin(self, username: str, cabinet: Cabinet | None = None) -> User:
        return self.user(username, role=User.Role.ADMIN, cabinet=cabinet)

    def doctor(self, username: str, cabinet: Cabinet) -> tuple[User, Doctor]:
        user = self.user(username, role=User.Role.DOCTOR, cabinet=cabinet)
        specialite, _ = Specialite.objects.get_or_create(name="Médecine générale")
        doctor = Doctor.objects.create(
            user=user,
            cabinet=cabinet,
            inp=f"INP{user.pk:05d}",
            gender=Doctor.Gender.MALE,
            specialiste=specialite,
        )
        return user, doctor

    def assistant(self, username: str, cabinet: Cabinet) -> tuple[User, Assistant]:
        user = self.user(username, role=User.Role.ASSISTANT, cabinet=cabinet)
        assistant = Assistant.objects.create(
            user=user,
            cabinet=cabinet,
            cin=f"CIN-{user.pk:05d}",
            gender=Assistant.Gender.FEMALE,
        )
        return user, assistant

    def patient(
        self,
        cabinet: Cabinet,
        cin: str,
        *,
        firstname: str = "Ahmed",
        lastname: str = "Benali",
        assurance: str = "",
    ) -> Patient:
        return Patient.objects.create(
            cabinet=cabinet,
            cin=cin,
            firstname=firstname,
            lastname=lastname,
            gender=Patient.Gender.MALE,
            age=35,
            assurance=assurance,
        )


def future_start(hour_offset: int = 1) -> timezone.datetime:
    """An aware `now + hour_offset` used as a valid RDV start."""
    return timezone.now() + timezone.timedelta(hours=hour_offset)


def make_start_end(
    start: timezone.datetime, minutes: int = 60
) -> tuple[timezone.datetime, timezone.datetime]:
    return start, start + timezone.timedelta(minutes=minutes)


def to_iso(start: timezone.datetime) -> str:
    return start.isoformat()


def login_payload(username: str, password: str = "password123") -> Callable[[], dict]:
    return lambda: {"username": username, "password": password}