from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Cabinet, Specialite, User


class Command(BaseCommand):
    help = (
        "Crée un jeu de données de démonstration : cabinet, spécialités et "
        "comptes admin / médecin / secrétaire. Idempotent."
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
        Specialite.objects.get_or_create(name="Médecine générale")
        Specialite.objects.get_or_create(name="Cardiologie")

        self._ensure_user(
            "admin",
            password,
            role=User.Role.ADMIN,
            cabinet=None,
            superuser=True,
            first_name="Admin",
        )
        self._ensure_user(
            "doctor1",
            password,
            role=User.Role.DOCTOR,
            cabinet=cabinet,
            first_name="Youssef",
            last_name="El Amrani",
        )
        self._ensure_user(
            "assistant1",
            password,
            role=User.Role.ASSISTANT,
            cabinet=cabinet,
            first_name="Salma",
            last_name="Bennani",
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
