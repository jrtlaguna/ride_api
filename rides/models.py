from django.conf import settings
from django.db import models
from django.utils import timezone


class Ride(models.Model):
    class Status(models.TextChoices):
        EN_ROUTE = "en-route", "En route"
        PICKUP = "pickup", "Pickup"
        DROPOFF = "dropoff", "Dropoff"

    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.EN_ROUTE
    )
    id_rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rides_as_rider",
        db_column="id_rider",
    )
    id_driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="rides_as_driver",
        db_column="id_driver",
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()

    class Meta:
        db_table = "ride"
        indexes = [
            models.Index(fields=["pickup_time"], name="ride_pickup_time_idx"),
            models.Index(
                fields=["status", "pickup_time"], name="ride_status_pickup_idx"
            ),
        ]

    def __str__(self):
        return f"Ride {self.id_ride} ({self.status})"


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name="ride_events",
        db_column="id_ride",
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "ride_event"
        indexes = [
            models.Index(
                fields=["id_ride", "-created_at"], name="ride_event_ride_dt_idx"
            ),
            models.Index(fields=["-created_at"], name="ride_event_created_idx"),
        ]

    def __str__(self):
        return f"RideEvent {self.id_ride_event} for ride {self.id_ride_id}"
