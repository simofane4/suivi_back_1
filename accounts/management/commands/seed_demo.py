from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Assistant, Cabinet, Doctor, Specialite, User


class Command(BaseCommand):
    help = (
        "Crée un jeu de données de démonstration : cabinet, spécialités, "
        "comptes admin / médecin / secrétaire et leurs profils. Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="password123",
            help="Mot de passe appliqué aux comptes de démo (défaut : password123).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]

        cabinet, _ = Cabinet.objects.get_or_create(
            number="CAB-001",
            defaults={"name": "Clinique Principale", "address": "Casablanca"},
        )

        generaliste, _ = Specialite.objects.get_or_create(name="Médecine générale")
        Specialite.objects.get_or_create(name="Cardiologie")

        self._ensure_user(
            "admin",
            password,
            role=User.Role.ADMIN,
            cabinet=None,
            superuser=True,
            first_name="Admin",
        )
        doctor_user = self._ensure_user(
            "doctor1",
            password,
            role=User.Role.DOCTOR,
            cabinet=cabinet,
            first_name="Youssef",
            last_name="El Amrani",
        )
        assistant_user = self._ensure_user(
            "assistant1",
            password,
            role=User.Role.ASSISTANT,
            cabinet=cabinet,
            first_name="Salma",
            last_name="Bennani",
        )

        Doctor.objects.get_or_create(
            user=doctor_user,
            defaults={
                "cabinet": cabinet,
                "inp": "INP00001",
                "gender": Doctor.Gender.MALE,
                "phone": "+212600000001",
                "address": "Casablanca",
                "specialiste": generaliste,
            },
        )
        Assistant.objects.get_or_create(
            user=assistant_user,
            defaults={
                "cabinet": cabinet,
                "cin": "CIN00001",
                "gender": Assistant.Gender.FEMALE,
                "phone": "+212600000002",
                "address": "Casablanca",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Seed terminé. Comptes : admin, doctor1, assistant1 "
                f"(mot de passe : {password})."
            )
        )

    def _ensure_user(
        self, username, password, *, role, cabinet, superuser=False,
        first_name="", last_name="",
    ):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "role": role,
                "cabinet": cabinet,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password(password)
            if superuser:
                user.is_staff = True
                user.is_superuser = True
            user.save()
        return user
