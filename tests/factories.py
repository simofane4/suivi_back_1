"""Factory definitions for generating test data using Factory Boy."""

import factory
from datetime import datetime, timedelta
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User

from cabinets.models import Cabinet, Specialite
from accounts.models import Doctor, Assistant
from patients.models import Patient, PatientFile
from clinical.models import Appointment, Ordonnance, ActeDemander, ActeFait, Medicament
from billing.models import Invoice


class SpecialiteFactory(DjangoModelFactory):
    """Factory for creating test Specialite instances."""

    class Meta:
        model = Specialite

    name = factory.Faker("word", locale="fr_FR")


class CabinetFactory(DjangoModelFactory):
    """Factory for creating test Cabinet instances."""

    class Meta:
        model = Cabinet

    number = factory.Sequence(lambda n: f"CAB-{n:05d}")
    name = factory.Faker("company", locale="fr_FR")
    address = factory.Faker("address", locale="fr_FR")


class UserFactory(DjangoModelFactory):
    """Factory for creating test User instances."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Faker("email")
    first_name = factory.Faker("first_name", locale="fr_FR")
    last_name = factory.Faker("last_name", locale="fr_FR")
    password = factory.PostGenerationMethodCall("set_password", "test12345")


class DoctorFactory(DjangoModelFactory):
    """Factory for creating test Doctor instances."""

    class Meta:
        model = Doctor

    user = factory.SubFactory(UserFactory)
    cabinet = factory.SubFactory(CabinetFactory)
    specialiste = factory.SubFactory(SpecialiteFactory)
    inp = factory.Sequence(lambda n: f"INP{n:08d}")
    gender = "Male"
    phone = factory.Faker("phone_number", locale="fr_FR")
    address = factory.Faker("address", locale="fr_FR")


class AssistantFactory(DjangoModelFactory):
    """Factory for creating test Assistant instances."""

    class Meta:
        model = Assistant

    user = factory.SubFactory(UserFactory)
    cabinet = factory.SubFactory(CabinetFactory)
    cin = factory.Sequence(lambda n: f"CIN{n:08d}")
    gender = "Female"
    phone = factory.Faker("phone_number", locale="fr_FR")
    address = factory.Faker("address", locale="fr_FR")


class PatientFactory(DjangoModelFactory):
    """Factory for creating test Patient instances."""

    class Meta:
        model = Patient

    cabinet = factory.SubFactory(CabinetFactory)
    cin = factory.Sequence(lambda n: f"CIN{n:08d}")
    firstname = factory.Faker("first_name", locale="fr_FR")
    lastname = factory.Faker("last_name", locale="fr_FR")
    gender = factory.Faker("random_element", elements=["Male", "Female"])
    age = factory.Faker("random_int", min=18, max=80)
    phone = factory.Faker("phone_number", locale="fr_FR")
    address = factory.Faker("address", locale="fr_FR")
    child = False


class PatientFileFactory(DjangoModelFactory):
    """Factory for creating test PatientFile instances."""

    class Meta:
        model = PatientFile

    patient = factory.SubFactory(PatientFactory)
    file = factory.django.FileField(filename="test_file.pdf")


class ActeDemanderFactory(DjangoModelFactory):
    """Factory for creating test ActeDemander instances."""

    class Meta:
        model = ActeDemander

    cabinet = factory.SubFactory(CabinetFactory)
    title = factory.Faker("word", locale="fr_FR")
    description = factory.Faker("text", max_nb_chars=200, locale="fr_FR")


class ActeFaitFactory(DjangoModelFactory):
    """Factory for creating test ActeFait instances."""

    class Meta:
        model = ActeFait

    cabinet = factory.SubFactory(CabinetFactory)
    title = factory.Faker("word", locale="fr_FR")
    description = factory.Faker("text", max_nb_chars=200, locale="fr_FR")


class MedicamentFactory(DjangoModelFactory):
    """Factory for creating test Medicament instances."""

    class Meta:
        model = Medicament

    cabinet = factory.SubFactory(CabinetFactory)
    name = factory.Faker("word", locale="fr_FR")
    description = factory.Faker("text", max_nb_chars=200, locale="fr_FR")


class AppointmentFactory(DjangoModelFactory):
    """Factory for creating test Appointment instances."""

    class Meta:
        model = Appointment

    cabinet = factory.SubFactory(CabinetFactory)
    patient = factory.SubFactory(PatientFactory, cabinet=factory.SelfAttribute("..cabinet"))
    date = factory.LazyFunction(lambda: (datetime.now() + timedelta(days=7)).date())
    start = factory.LazyFunction(lambda: datetime.strptime("09:00", "%H:%M").time())
    end = factory.LazyFunction(lambda: datetime.strptime("10:00", "%H:%M").time())
    description = factory.Faker("text", max_nb_chars=100, locale="fr_FR")


class OrdonnanceFactory(DjangoModelFactory):
    """Factory for creating test Ordonnance instances."""

    class Meta:
        model = Ordonnance

    appointment = factory.SubFactory(AppointmentFactory)
    cabinet = factory.SelfAttribute("appointment.cabinet")
    description = factory.Faker("text", max_nb_chars=200, locale="fr_FR")


class InvoiceFactory(DjangoModelFactory):
    """Factory for creating test Invoice instances."""

    class Meta:
        model = Invoice

    appointment = factory.SubFactory(AppointmentFactory)
    date = factory.Faker("date_time_this_year")
    recipient = factory.SubFactory(UserFactory)
    amount = factory.Faker("pyint", min_value=1, max_value=10000)
    payed = False
