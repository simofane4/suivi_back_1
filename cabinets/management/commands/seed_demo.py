"""Populate the database with demo data.

    python manage.py seed_demo
    python manage.py seed_demo --cabinets 5 --patients-per-cabinet 20
    python manage.py seed_demo --flush

Running the command twice changes nothing. That is achieved with two rules:

* Faker and `random` are seeded, so the cosmetic fields (names, addresses) come
  out identical on every run.
* Every record is looked up by a **deterministic** natural key -- cabinet
  number, username, CIN -- never by a freshly invented random value. The
  original `createdata` command inserted 45 specialities, 16 cabinets and 750
  patients on every single run, and located the rows it had just created with
  `Model.objects.last()`, which attaches the wrong record as soon as two writes
  interleave.

This lives in the `cabinets` app because cabinets are the root of the tenancy
model, and a management command must live inside an installed app.
"""

import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from accounts.models import Assistant, Doctor
from billing.models import Invoice
from cabinets.models import Cabinet, Specialite
from clinical.models import ActeDemander, ActeFait, Appointment, Medicament, Ordonnance
from common.constants import GENDER_FEMALE, GENDER_MALE
from patients.models import Patient

SEED = 20261002
DEMO_PASSWORD = "demo12345"

# The 45 specialities from the original data set, kept verbatim so existing
# fixtures keep matching.
SPECIALITES = [
    "L allergologie ou l immunologie",
    "L anesthésiologie",
    "Landrologie",
    "La cardiologie",
    "La chirurgie",
    "La chirurgie cardiaque",
    "La chirurgie esthétique,plastique et reconstructive",
    "La chirurgie générale",
    "La chirurgie maxillo-faciale",
    "La chirurgie pédiatrique",
    "La chirurgie thoracique",
    "La chirurgie vasculaire",
    "La neurochirurgie",
    "La dermatologie",
    "L endocrinologie",
    "La gastro-entérologie",
    "La gériatrie",
    "La gynécologie",
    "L hématologie",
    "L hépatologie",
    "L infectiologie",
    "La médecine aiguë",
    "La médecine du travail",
    "La médecine générale",
    "La médecine interne",
    "La médecine nucléaire",
    "La médecine palliative",
    "La médecine physique",
    "La médecine préventive",
    "La néonatologie",
    "La néphrologie",
    "La neurologie",
    "L odontologie",
    "L oncologie",
    "L obstétrique",
    "L ophtalmologie",
    "L orthopédie",
    "L Oto-rhino-laryngologie",
    "La pédiatrie",
    "La pneumologie",
    "La psychiatrie",
    "La radiologie",
    "La radiothérapie",
    "La rhumatologie",
    "L urologie",
]

GENDERS = [GENDER_FEMALE, GENDER_MALE]

ACTES = [
    "Consultation generale",
    "Consultation specialisee",
    "Controle post-operatoire",
    "Bilan sanguin",
    "Radio thoracique",
    "Ponction lombaire",
    "Certificat medical",
    "Renouvellement d'ordonnance",
]

MEDICAMENTS = [
    "Paracetamol 500mg",
    "Amoxicilline 1g",
    "Ibuprofene 400mg",
    "Omeprazole 20mg",
    "Metformine 850mg",
    "Amlodipine 5mg",
    "Salbutamol spray",
    "Cetirizine 10mg",
]

FLUSH_ORDER = (
    Invoice,
    Ordonnance,
    Appointment,
    ActeDemander,
    ActeFait,
    Medicament,
    Patient,
    Doctor,
    Assistant,
)


class Command(BaseCommand):
    help = "Create idempotent demo data across all apps."

    def add_arguments(self, parser):
        parser.add_argument("--cabinets", type=int, default=3)
        parser.add_argument("--patients-per-cabinet", type=int, default=25)
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing clinic data before seeding.",
        )

    def handle(self, *args, **options):
        # Seeded so cosmetic fields are stable between runs; the idempotency
        # itself rests on the deterministic natural keys below.
        Faker.seed(SEED)
        self.faker = Faker()
        self.random = random.Random(SEED)

        if options["flush"]:
            self._flush()

        with transaction.atomic():
            specialites = self._seed_specialites()
            for index in range(1, options["cabinets"] + 1):
                cabinet = self._seed_cabinet(index)
                self._seed_staff(cabinet, index, specialites)
                self._seed_catalogue(cabinet)
                self._seed_patients(cabinet, index, options["patients_per_cabinet"])

        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"  staff password: {DEMO_PASSWORD}")

    # --- steps ------------------------------------------------------------

    def _flush(self):
        self.stdout.write(self.style.WARNING("Flushing existing clinic data..."))
        for model in FLUSH_ORDER:
            deleted, _ = model.objects.all().delete()
            if deleted:
                self.stdout.write(f"  {model.__name__}: {deleted} deleted")
        User.objects.filter(is_superuser=False).delete()

    def _seed_specialites(self):
        specialites = []
        for name in SPECIALITES:
            specialite, _ = Specialite.objects.get_or_create(name=name)
            specialites.append(specialite)
        return specialites

    def _seed_cabinet(self, index):
        number = f"DEMO-{index:03d}"
        cabinet, created = Cabinet.objects.get_or_create(
            number=number,
            defaults={
                "name": f"Cabinet Demo {index}",
                "address": self.faker.address(),
            },
        )
        if created:
            self.stdout.write(f"  created {cabinet}")
        return cabinet

    def _seed_staff(self, cabinet, index, specialites):
        for slot in range(1, 3):
            self._create_doctor(cabinet, index, slot, specialites)
        self._create_assistant(cabinet, index, 1)

    def _create_doctor(self, cabinet, cabinet_index, slot, specialites):
        user, created = self._staff_user(
            username=f"demo_doc_{cabinet_index}_{slot}",
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
        )
        if not created:
            return

        Doctor.objects.get_or_create(
            user=user,
            defaults={
                "cabinet": cabinet,
                "inp": f"DEMO-INP-{cabinet_index}{slot:02d}",
                "gender": self.random.choice(GENDERS),
                "phone": self.faker.phone_number(),
                "address": self.faker.address(),
                "specialiste": self.random.choice(specialites),
            },
        )

    def _create_assistant(self, cabinet, cabinet_index, slot):
        user, created = self._staff_user(
            username=f"demo_ast_{cabinet_index}_{slot}",
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
        )
        if not created:
            return

        Assistant.objects.get_or_create(
            user=user,
            defaults={
                "cabinet": cabinet,
                "cin": f"DEMO-CIN-{cabinet_index}{slot:02d}",
                "gender": self.random.choice(GENDERS),
                "phone": self.faker.phone_number(),
                "address": self.faker.address(),
            },
        )

    def _staff_user(self, *, username, first_name, last_name):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": f"{username}@example.com",
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user, created

    def _seed_catalogue(self, cabinet):
        for title in ACTES:
            ActeDemander.objects.get_or_create(
                cabinet=cabinet,
                title=title,
                defaults={"description": self.faker.sentence()},
            )
            ActeFait.objects.get_or_create(
                cabinet=cabinet,
                title=title,
                defaults={"description": self.faker.sentence()},
            )
        for name in MEDICAMENTS:
            Medicament.objects.get_or_create(
                cabinet=cabinet,
                name=name,
                defaults={"description": self.faker.sentence()},
            )

    def _seed_patients(self, cabinet, cabinet_index, count):
        created = 0
        for slot in range(1, count + 1):
            _, was_created = Patient.objects.get_or_create(
                cabinet=cabinet,
                cin=f"DEMO-P-{cabinet_index:02d}{slot:04d}",
                defaults={
                    "firstname": self.faker.first_name(),
                    "lastname": self.faker.last_name(),
                    "gender": self.random.choice(GENDERS),
                    "age": self.random.randint(1, 85),
                    "phone": self.faker.phone_number(),
                    "address": self.faker.address(),
                },
            )
            created += int(was_created)
        self.stdout.write(f"  {cabinet.name}: {created} new patient(s)")
