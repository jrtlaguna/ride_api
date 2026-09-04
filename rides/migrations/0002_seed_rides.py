import random
from datetime import timedelta

from django.db import migrations
from django.utils import timezone

SEED_DOMAIN = "seed.example.com"
RIDE_COUNT = 50

STATUSES = ["en-route", "pickup", "dropoff"]

EVENT_DESCRIPTIONS = [
    "Ride requested",
    "Driver assigned",
    "Status changed to en-route",
    "Driver arrived at pickup",
    "Rider picked up",
    "Status changed to dropoff",
    "Ride completed",
]

LAT_RANGE = (14.40, 14.72)
LNG_RANGE = (120.92, 121.12)


def _seed_user_ids(User):
    return list(
        User.objects.filter(email__endswith=f"@{SEED_DOMAIN}")
        .order_by("id_user")
        .values_list("id_user", "role")
    )


def create_rides(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Ride = apps.get_model("rides", "Ride")
    RideEvent = apps.get_model("rides", "RideEvent")

    users = _seed_user_ids(User)
    riders = [pk for pk, role in users if role == "rider"]
    drivers = [pk for pk, role in users if role == "driver"]
    if not riders or not drivers:
        return
    if Ride.objects.filter(id_rider__in=riders).exists():
        return

    rng = random.Random(20260902)
    now = timezone.now()

    Ride.objects.bulk_create(
        [
            Ride(
                status=rng.choice(STATUSES),
                id_rider_id=rng.choice(riders),
                id_driver_id=rng.choice(drivers),
                pickup_latitude=round(rng.uniform(*LAT_RANGE), 6),
                pickup_longitude=round(rng.uniform(*LNG_RANGE), 6),
                dropoff_latitude=round(rng.uniform(*LAT_RANGE), 6),
                dropoff_longitude=round(rng.uniform(*LNG_RANGE), 6),
                # Spread backwards in time so ordering by pickup_time is varied.
                pickup_time=now - timedelta(hours=rng.uniform(0, 24 * 30)),
            )
            for _ in range(RIDE_COUNT)
        ]
    )

    events = []
    for ride in Ride.objects.filter(id_rider__in=riders).order_by("id_ride"):
        for _ in range(rng.randint(1, 3)):
            events.append(
                RideEvent(
                    id_ride_id=ride.id_ride,
                    description=rng.choice(EVENT_DESCRIPTIONS),
                    created_at=now - timedelta(hours=rng.uniform(0, 23)),
                )
            )
        for _ in range(rng.randint(2, 4)):
            events.append(
                RideEvent(
                    id_ride_id=ride.id_ride,
                    description=rng.choice(EVENT_DESCRIPTIONS),
                    created_at=now - timedelta(days=rng.uniform(2, 60)),
                )
            )
    RideEvent.objects.bulk_create(events)


def delete_rides(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Ride = apps.get_model("rides", "Ride")
    rider_ids = list(
        User.objects.filter(email__endswith=f"@{SEED_DOMAIN}").values_list(
            "id_user", flat=True
        )
    )

    Ride.objects.filter(id_rider__in=rider_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0001_initial"),
        ("accounts", "0002_seed_users"),
    ]

    operations = [migrations.RunPython(create_rides, delete_rides)]
