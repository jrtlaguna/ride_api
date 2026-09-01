from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations

SEED_DOMAIN = "seed.example.com"
RIDER_COUNT = 10
DRIVER_COUNT = 10


def _admin_email():
    return (settings.ADMIN_USER_EMAIL or "").strip().lower()


def create_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    unusable = make_password(None)

    rows = [
        User(
            email=f"rider{i:02d}@{SEED_DOMAIN}",
            first_name=f"Rider{i:02d}",
            last_name="Seed",
            role="rider",  # User.Role is unavailable on historical models
            password=unusable,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        for i in range(1, RIDER_COUNT + 1)
    ] + [
        User(
            email=f"driver{i:02d}@{SEED_DOMAIN}",
            first_name=f"Driver{i:02d}",
            last_name="Seed",
            role="driver",
            password=unusable,
            is_active=True,
            is_staff=False,
            is_superuser=False,
        )
        for i in range(1, DRIVER_COUNT + 1)
    ]

    # ignore_conflicts keeps a re-run harmless if the rows already exist.
    User.objects.bulk_create(rows, ignore_conflicts=True)

    # The admin is the one seeded account that can log in, so it is created only
    # when a password is supplied via ADMIN_USER_PASSWORD. No password, no
    # account -- rather than a privileged user with a default credential.
    email, password = _admin_email(), settings.ADMIN_USER_PASSWORD
    if not (email and password):
        return

    defaults = {
        "first_name": "Admin",
        "last_name": "Seed",
        "role": "admin",
        "password": make_password(password),
        "is_active": True,
        "is_staff": True,
        "is_superuser": True,
    }
    # update_or_create rather than bulk_create/ignore_conflicts: if the row
    # already exists, ignore_conflicts would silently keep a stale hash and
    # ADMIN_USER_PASSWORD would no longer match what is stored. Re-applying this
    # migration is therefore also how you rotate the seeded admin's password.
    # Email is lowercased in _admin_email: the historical model has no save()
    # override, so the normalisation on the real model does not apply here.
    User.objects.update_or_create(email=email, defaults=defaults)


def delete_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Token = apps.get_model("authtoken", "Token")
    LogEntry = apps.get_model("admin", "LogEntry")

    doomed = User.objects.filter(email__endswith=f"@{SEED_DOMAIN}")
    email = _admin_email()
    if email:
        doomed = doomed | User.objects.filter(email=email)
    ids = list(doomed.values_list("id_user", flat=True))

    Token.objects.filter(user_id__in=ids).delete()
    LogEntry.objects.filter(user_id__in=ids).delete()
    User.objects.filter(id_user__in=ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("authtoken", "0001_initial"),
        ("admin", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_users, delete_users)]
