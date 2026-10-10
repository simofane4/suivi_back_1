"""Create the fixed logins the Angular sign-in page advertises.

    python manage.py seed_test_users
    python manage.py seed_test_users --reset-passwords

The sign-in screen ships three autofill buttons (`admin@hospital.org`,
`doctor@hospital.org`, `patient@hospital.org`). Without matching accounts they
all fail with a 401 and there is no way to reach any screen by hand, because
every seeded username is random.

Idempotent: each account is looked up by its username and each profile by the
natural key the API filters on, so running this twice changes nothing except
when `--reset-passwords` is passed.

Patients are the awkward case: `patients.Patient` has no `User` behind it, and
`POST /api/auth/token/` only issues tokens for `auth_user` rows. A patient is
therefore seeded as a *record*, not as a login -- see the printed summary.
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Assistant, Doctor
from cabinets.models import Cabinet, Specialite
from patients.models import Patient

ADMIN_PASSWORD = "admin@123"
DOCTOR_PASSWORD = "doctor@123"
ASSISTANT_PASSWORD = "assistant@123"

CABINET_NUMBER = "TEST-001"
SPECIALITE_NAME = "La médecine générale"

# `Doctor.specialiste` ("spécialiste") is one letter away from the far more
# common `specialite` ("spécialité"), and the API spells it `specialiste`.
# Resolving the FK off the model keeps that distinction from being a typo.
SPECIALITE_FIELD = next(
    field.name for field in Doctor._meta.get_fields() if field.name.startswith("special")
)

ACCOUNTS = {
    "admin": {
        "username": "admin@hospital.org",
        "email": "admin@hospital.org",
        "first_name": "Admin",
        "last_name": "Test",
        "password": ADMIN_PASSWORD,
        "superuser": True,
    },
    "doctor": {
        "username": "doctor@hospital.org",
        "email": "doctor@hospital.org",
        "first_name": "Doctor",
        "last_name": "Test",
        "password": DOCTOR_PASSWORD,
    },
    "assistant": {
        "username": "assistant@hospital.org",
        "email": "assistant@hospital.org",
        "first_name": "Assistant",
        "last_name": "Test",
        "password": ASSISTANT_PASSWORD,
    },
}

PATIENTS = [
    {
        "cin": "TEST-P-0001",
        "firstname": "Patient",
        "lastname": "Test",
        "gender": "Male",
        "age": 45,
        "phone": "+212600000101",
        "address": "1 Test Street",
    },
    {
        "cin": "TEST-P-0002",
        "firstname": "Patiente",
        "lastname": "Test",
        "gender": "Female",
        "age": 32,
        "phone": "+212600000102",
        "address": "2 Test Street",
    },
]


class Command(BaseCommand):
    help = "Create the fixed admin/doctor/assistant logins and a few patient records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Re-apply the documented passwords to existing accounts.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        reset = options["reset_passwords"]

        cabinet = self._cabinet()
        specialite = self._specialite()

        admin = self._account(ACCOUNTS["admin"], reset)
        if admin["created"] or reset:
            admin["user"].set_password(ACCOUNTS["admin"]["password"])
            admin["user"].save()
            admin["reset"] = True

        doctor_user = self._account(ACCOUNTS["doctor"], reset)
        doctor, doctor_created = self._doctor(doctor_user["user"], cabinet, specialite)
        if doctor_user["created"] or reset:
            doctor_user["user"].set_password(ACCOUNTS["doctor"]["password"])
            doctor_user["user"].save()

        assistant_user = self._account(ACCOUNTS["assistant"], reset)
        assistant, assistant_created = self._assistant(assistant_user["user"], cabinet)
        if assistant_user["created"] or reset:
            assistant_user["user"].set_password(ACCOUNTS["assistant"]["password"])
            assistant_user["user"].save()

        patients = self._patients(cabinet)

        self.stdout.write(self.style.SUCCESS("Test data ready."))
        self.stdout.write(f"  cabinet:   {cabinet.name} (#{cabinet.number})")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  LOGINS"))
        self.stdout.write(
            f"    admin      {ACCOUNTS['admin']['username']} / {ACCOUNTS['admin']['password']}"
            f"  {'(new)' if admin['created'] else ''}"
        )
        self.stdout.write(
            f"    doctor     {ACCOUNTS['doctor']['username']} / {ACCOUNTS['doctor']['password']}"
            f"  {'(new)' if doctor_created else ''}"
        )
        self.stdout.write(
            f"    assistant  {ACCOUNTS['assistant']['username']} / {ACCOUNTS['assistant']['password']}"
            f"  {'(new)' if assistant_created else ''}"
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  PATIENT RECORDS (no login)"))
        for patient in patients:
            self.stdout.write(
                f"    {patient.cin}  {patient.firstname} {patient.lastname}  {patient.phone}"
            )
        self.stdout.write(
            self.style.WARNING(
                "  patients.Patient has no User, so patient@hospital.org cannot log in;"
                " the API only issues tokens for auth_user rows."
            )
        )

    def _cabinet(self) -> Cabinet:
        cabinet, created = Cabinet.objects.get_or_create(
            number=CABINET_NUMBER,
            defaults={"name": "Cabinet Test", "address": "1 Cabinet Street"},
        )
        if created:
            self.stdout.write(f"  created cabinet {cabinet}")
        return cabinet

    def _specialite(self) -> Specialite:
        specialite, _ = Specialite.objects.get_or_create(name=SPECIALITE_NAME)
        return specialite

    def _account(self, spec: dict, reset: bool):
        """`get_or_create` on the username, which is the API's natural key."""
        user, created = User.objects.get_or_create(
            username=spec["username"],
            defaults={
                "email": spec["email"],
                "first_name": spec["first_name"],
                "last_name": spec["last_name"],
            },
        )
        changed = False
        for field in ("email", "first_name", "last_name"):
            if getattr(user, field) != spec[field]:
                setattr(user, field, spec[field])
                changed = True

        if spec.get("superuser") and not (user.is_superuser and user.is_staff):
            user.is_superuser = True
            user.is_staff = True
            changed = True
        if not user.is_active:
            user.is_active = True
            changed = True

        if changed:
            user.save()
        return {"user": user, "created": created, "changed": changed or reset}

    def _doctor(self, user: User, cabinet: Cabinet, specialite: Specialite):
        """`inp` and `phone` are globally unique on Doctor."""
        existing = Doctor.objects.filter(user=user).first()
        if existing:
            return existing, False

        doctor = Doctor.objects.create(
            user=user,
            cabinet=cabinet,
            inp="TEST-INP-001",
            gender="Male",
            phone="+212600000001",
            address="1 Doctor Street",
            **{SPECIALITE_FIELD: specialite},
        )
        self.stdout.write(f"  created doctor {doctor}")
        return doctor, True

    def _assistant(self, user: User, cabinet: Cabinet):
        assistant, created = Assistant.objects.get_or_create(
            user=user,
            defaults={
                "cabinet": cabinet,
                "cin": "TEST-CIN-001",
                "gender": "Female",
                "phone": "+212600000002",
                "address": "2 Assistant Street",
            },
        )
        if created:
            self.stdout.write(f"  created assistant {assistant}")
        return assistant, created

    def _patients(self, cabinet: Cabinet):
        patients = []
        for spec in PATIENTS:
            # `cin` is the natural key inside a cabinet, so it stays out of
            # `defaults` -- a key present in both would silently win there.
            fields = {k: v for k, v in spec.items() if k != "cin"}
            patient, _ = Patient.objects.get_or_create(
                cabinet=cabinet,
                cin=spec["cin"],
                defaults=fields,
            )
            patients.append(patient)
        return patients