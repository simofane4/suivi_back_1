from datetime import datetime, time as dtime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone as dj_timezone

from accounts.models import Assistant, Cabinet, Doctor, Specialite, User
from appointments.models import Appointment
from billing.models import Invoice, Payment
from catalog.models import ActeDemander, ActeFait, Medicament
from patients.models import Allergie, Antecedent, Observation, Patient
from prescriptions.models import Ordonnance, OrdonnanceLine

_MEDICAMENTS = [
    ("Paracétamol", "باراسيتامول", "Comprimé", "500 mg", "Antalgique / antipyrétique"),
    ("Ibuprofène", "إيبوبروفين", "Comprimé", "400 mg", "Anti-inflammatoire"),
    ("Amoxicilline", "أموكسيسيلين", "Gélule", "500 mg", "Antibiotique"),
    ("Azithromycine", "أزيثروميسين", "Comprimé", "250 mg", "Antibiotique macrolide"),
    ("Oméprazole", "أوميبرازول", "Gélule", "20 mg", "IPPE gastrique"),
    ("Metformine", "ميتفورمين", "Comprimé", "850 mg", "Antidiabétique"),
    ("Losartan", "لوسارتان", "Comprimé", "50 mg", "Antihypertenseur"),
    ("Amlodipine", "أملوديبين", "Comprimé", "5 mg", "Inhibiteur calcique"),
    ("Salbutamol", "سالبوتامول", "Aérosol", "100 µg/dose", "Bronchodilatateur"),
    ("Amoxicilline+Ac. clav.", "أموكسيسيلين+حامض الكلافولانيك", "Comprimé", "1 g", "Antibiotique"),
    ("Ciprofloxacine", "سيبروفلوكساسين", "Comprimé", "500 mg", "Antibiotique quinolone"),
    ("Diclofénac", "ديكلوفيناك", "Gel", "1 %", "Antalgique local"),
    ("Vitamine D3", "فيتامين د3", "Ampoule", "200 000 UI", "Supplémentation"),
    ("Fer + acide folique", "حديد + حمض الفوليك", "Comprimé", "65 mg", "Anti-anémique"),
    ("Prednisolone", "بريدنيزولون", "Comprimé", "5 mg", "Corticoïde"),
    ("Lévothyroxine", "ليفوثيروكسين", "Comprimé", "50 µg", "Hormone thyroïdienne"),
    ("Clarithromycine", "كلاريثروميسين", "Comprimé", "500 mg", "Antibiotique macrolide"),
    ("Ranitidine", "رانيتيدين", "Comprimé", "150 mg", "Anti-ulcéreux"),
    ("Dompéridone", "دومبيريدون", "Comprimé", "10 mg", "Antinauséeux"),
    ("Fluconazole", "فلوكونازول", "Gélule", "150 mg", "Antifongique"),
]

_PATIENTS = [
    ("BE123456", "Ahmed", "Benali", "M", 45, "CNOPS", "AD-881001", "Casablanca"),
    ("YH224567", "Fatima", "El Idrissi", "F", 38, "CNSS", "EC-221004", "Casablanca"),
    ("CA335678", "Karim", "Tazi", "M", 28, "", "", "Rabat"),
    ("BZ446789", "Salma", "Alami", "F", 33, "CNAMGS", "CG-992013", "Casablanca"),
    ("DX557890", "Rachid", "Bennis", "M", 52, "CNOPS", "AD-881088", "Mohammedia"),
    ("FE668901", "Nadia", "Cherkaoui", "F", 24, "CNSS", "EC-221117", "Casablanca"),
    ("GB779012", "Omar", "Berrada", "M", 61, "MUTUELLE", "MU-555901", "Casablanca"),
    ("HC880123", "Hind", "Filali", "F", 41, "CNOPS", "AD-881201", "Temara"),
    ("JA991234", "Mehdi", "Kabbaj", "M", 36, "", "", "Casablanca"),
    ("KC002345", "Imane", "Zerhouni", "F", 29, "CNSS", "EC-221204", "Aïn Sebaâ"),
]

_ANTECEDENTS = [
    "Hypertension artérielle",
    "Diabète de type 2",
    "Asthme",
    "Allergie médicamenteuse",
    "Chirurgie abdominale (2019)",
    "Migraine chronique",
]

_ALLERGIES = ["Pénicilline", "Aspirine", "Pollen", "Arachides", "Iode"]

_OBSERVATIONS = [
    ("I10", "Hypertension essentielle", "PA 150/95 ; réévaluer sous traitement."),
    ("E11", "Diabète type 2", "HbA1c 7,8 % ; adapter la metformine."),
    ("J45", "Asthme", "Sibilants aux bases ; bronchodilatateur à la demande."),
    ("K29", "Gastrite", "Épigastralgie ; IPP 4 semaines."),
]

_ACTES_DEMANDES = [
    "NFS + CRP",
    "Glycémie à jeun + HbA1c",
    "Bilan lipidique",
    "ECG de repos",
    "Echographie abdominale",
    "Radiographie thoracique",
]

_ACTES_FAITS = [
    "Consultation de médecine générale",
    "Consultation de suivi HTA",
    "Consultation de suivi diabète",
    "Consultation pour infection respiratoire",
    "Petit acte de soins (pansement)",
    "Accompagnement vaccinal",
]


class Command(BaseCommand):
    help = (
        "Crée un jeu de données de démonstration conforme à MVP-PLAN.md §7 : "
        "cabinet Casablanca, médecin + secrétaire, ~10 patients marocains, "
        "20 médicaments FR/AR, RDV, factures et ordonnances. Idempotent."
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
        cardiologue, _ = Specialite.objects.get_or_create(name="Cardiologie")

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

        doctor, _ = Doctor.objects.get_or_create(
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

        self._seed_catalog(cabinet)
        patients = self._seed_patients(cabinet)
        for patient in patients:
            self._seed_dossier(patient)

        appointments = self._seed_appointments(cabinet, doctor, patients)
        self._seed_ordonnances(cabinet, appointments, patients)
        self._seed_billing(cabinet, appointments, patients, doctor_user)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed terminé. Comptes : admin, doctor1, assistant1 "
                f"(mot de passe : {password}). Cabinet : {cabinet.name}."
            )
        )

    # ------------------------------------------------------------------ #

    def _seed_catalog(self, cabinet):
        for name_fr, name_ar, form, dosage, description in _MEDICAMENTS:
            Medicament.objects.get_or_create(
                cabinet=cabinet,
                name=name_fr,
                defaults={
                    "name_fr": name_fr,
                    "name_ar": name_ar,
                    "form": form,
                    "dosage": dosage,
                    "description": description,
                },
            )
        for title in _ACTES_DEMANDES:
            ActeDemander.objects.get_or_create(
                cabinet=cabinet,
                title=title,
            )
        for title in _ACTES_FAITS:
            ActeFait.objects.get_or_create(cabinet=cabinet, title=title)

    def _seed_patients(self, cabinet):
        patients = []
        for num, (cin, first, last, gender, age, assurance, adh, city) in enumerate(
            _PATIENTS
        ):
            patient, _ = Patient.objects.get_or_create(
                cabinet=cabinet,
                cin=cin,
                defaults={
                    "firstname": first,
                    "lastname": last,
                    "gender": gender,
                    "age": age,
                    "phone": f"+21261{num:07d}",
                    "address": city,
                    "assurance": assurance,
                    "numero_adherent": adh,
                },
            )
            patients.append(patient)
        return patients

    def _seed_dossier(self, patient):
        for label in _ANTECEDENTS[:4]:
            Antecedent.objects.get_or_create(
                patient=patient,
                label=label,
                defaults={"notes": "Antécédent déclaré."},
            )
        for name in _ALLERGIES[:3]:
            Allergie.objects.get_or_create(
                patient=patient,
                name=name,
                defaults={"severity": Allergie.Severity.MODEREE},
            )
        code, label, notes = _OBSERVATIONS[patient.pk % len(_OBSERVATIONS)]
        Observation.objects.get_or_create(
            patient=patient,
            diagnostic=code,
            version=1,
            defaults={"diagnostic_label": label, "notes": notes},
        )

    def _seed_appointments(self, cabinet, doctor, patients):
        appointments = []
        today = dj_timezone.localdate()
        hours = (9, 10, 11, 14, 15, 16, 9, 10, 11, 14)

        for idx, patient in enumerate(patients):
            if idx % 3 == 2:
                date = today  # today's agenda items
                day_offset = 0
            else:
                day_offset = (idx % 3) + 1
                date = today + timedelta(days=day_offset)
            start_h = hours[idx % len(hours)]
            start_naive = datetime.combine(date, dtime(start_h, 0))
            start = dj_timezone.make_aware(start_naive)
            end = start + timedelta(hours=1)
            status = Appointment.Status.SCHEDULED
            if day_offset == 0 and idx % 2 == 0:
                status = Appointment.Status.CONFIRMED
            appointment, _ = Appointment.objects.get_or_create(
                cabinet=cabinet,
                patient=patient,
                doctor=doctor,
                start=start,
                end=end,
                defaults={
                    "reason": "Consultation de suivi"
                    if patient.assurance
                    else "Consultation",
                    "status": status,
                },
            )
            appointments.append(appointment)
        return appointments

    def _seed_ordonnances(self, cabinet, appointments, patients):
        ordonnance_created = 0
        for idx, appointment in enumerate(appointments[:6]):
            if idx % 4 == 3:
                continue
            acte_fait = ActeFait.objects.filter(cabinet=cabinet).first()
            acte_demander = ActeDemander.objects.filter(cabinet=cabinet).first()
            ordonnance, created = Ordonnance.objects.get_or_create(
                cabinet=cabinet,
                appointment=appointment,
                defaults={
                    "acte_demander": acte_demander,
                    "acte_fait": acte_fait,
                    "description": (
                        "Prendre les médicaments conformément à la posologie "
                        "et revenir en consultation de contrôle."
                    ),
                },
            )
            if created:
                ordonnance_created += 1
            lines = Medicament.objects.filter(cabinet=cabinet).order_by("id")
            for line_med in lines[: (idx % 3) + 1]:
                OrdonnanceLine.objects.get_or_create(
                    ordonnance=ordonnance,
                    medicament=line_med,
                    defaults={
                        "dosage": line_med.dosage,
                        "duration": f"{3 + (idx % 3) * 2} jours",
                    },
                )
        return ordonnance_created

    def _seed_billing(self, cabinet, appointments, patients, recipient):
        invoiced = 0
        for idx, appointment in enumerate(appointments[:8]):
            if idx % 5 == 4:
                continue  # one appointment intentionally left unbilled
            patient = appointment.patient
            amount = Decimal(f"{100.00 + (idx % 5) * 50.00:.2f}")
            organisme_ratio = 0
            if patient.assurance in ("CNOPS", "CNAMGS", "FAR"):
                organisme_ratio = 80
            elif patient.assurance == "CNSS":
                organisme_ratio = 70

            invoice, created = Invoice.objects.get_or_create(
                cabinet=cabinet,
                appointment=appointment,
                defaults={
                    "amount": amount,
                    "organisme_ratio": organisme_ratio,
                    "recipient": recipient,
                },
            )
            if created:
                invoiced += 1
                oracle = idx % 3
                if oracle == 1:
                    # one partial payment -> shows a leftover
                    Payment.objects.create(
                        invoice=invoice,
                        amount=amount / 2,
                        kind=Payment.Kind.PATIENT,
                        method=Payment.Method.CARD,
                        created_by=recipient,
                        paid_at=appointment.start,
                    )
                elif oracle == 2 and organisme_ratio:
                    # insurance pays its share, patient share is taken in cash
                    Payment.objects.create(
                        invoice=invoice,
                        amount=invoice.organisme_share,
                        kind=Payment.Kind.ORGANISME,
                        method=Payment.Method.CHEQUE,
                        created_by=recipient,
                        paid_at=appointment.end,
                    )
                    Payment.objects.create(
                        invoice=invoice,
                        amount=invoice.patient_share,
                        kind=Payment.Kind.PATIENT,
                        method=Payment.Method.CASH,
                        created_by=recipient,
                        paid_at=invoice.date,
                    )
                # oracle == 0 -> left unpaid on purpose
                invoice.refresh_status()
        return invoiced

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