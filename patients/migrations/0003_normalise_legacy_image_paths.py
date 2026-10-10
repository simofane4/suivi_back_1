"""Normalise the legacy `img` values onto the current storage layout.

Three incompatible formats are stored in the legacy rows:

    media/patient/default.png          relative, with a doubled `media/` prefix
    /media/media/doctor/default.png    absolute, with a doubled `media/` prefix
    default.png                        bare filename

`ImageField` stores a name *relative to* `MEDIA_ROOT` and builds its URL as
`MEDIA_URL + name`. The old `upload_to` nested under a second `media/`
directory, which is why every stored value carries that extra prefix. Stripping
the leading `/` and any repeated `media/` segments leaves a correct relative
name, so `.url` resolves to `/media/<name>`.

A bare filename is left alone: there is no way to know which subdirectory it
was meant for, and dropping it is the safe choice.

Nothing is deleted; rows already correct are skipped.
"""

from django.db import migrations


def normalise_image_paths(apps, schema_editor):
    Patient = apps.get_model("patients", "Patient")
    Doctor = apps.get_model("accounts", "Doctor")
    Assistant = apps.get_model("accounts", "Assistant")

    def rewrite(model, field):
        updated = 0
        for obj in model.objects.order_by("pk").iterator():
            stored = getattr(obj, field)
            # In a data migration the attribute is a FieldFile, not a str.
            value = (getattr(stored, "name", None) or str(stored) or "").strip()

            cleaned = value.lstrip("/")
            stripped_any = cleaned != value
            while cleaned.startswith("media/"):
                cleaned = cleaned[len("media/") :]
                stripped_any = True

            if not cleaned or not stripped_any:
                continue

            # Assign the bare name; FieldFile rendering adds MEDIA_URL back.
            setattr(obj, field, cleaned)
            obj.save(update_fields=[field])
            updated += 1
        return updated

    total = rewrite(Patient, "img") + rewrite(Doctor, "img") + rewrite(Assistant, "img")
    if total:
        print(f"  patients: normalised {total} legacy image path(s)")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0002_timestamps_per_cabinet_uniqueness_and_indexes"),
    ]

    operations = [
        migrations.RunPython(normalise_image_paths, noop),
    ]
