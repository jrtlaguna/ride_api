from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.models import User
from rides.models import Ride, RideEvent


class RideUserSerializer(serializers.ModelSerializer):
    """Rider or driver as embedded in a ride payload."""

    class Meta:
        model = User
        fields = (
            "id_user",
            "role",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        )
        read_only_fields = fields


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ("id_ride_event", "id_ride", "description", "created_at")


class RideSerializer(serializers.ModelSerializer):
    """Read representation: rider, driver and the last 24h of events inline."""

    id_rider = RideUserSerializer(read_only=True)
    id_driver = RideUserSerializer(read_only=True)
    todays_ride_events = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = (
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "todays_ride_events",
        )

    @extend_schema_field(RideEventSerializer(many=True))
    def get_todays_ride_events(self, obj):
        # Populated by the view's Prefetch(to_attr=...). Read via getattr so a
        # ride serialized outside that queryset degrades to an empty list rather
        # than silently issuing a query per row.
        events = getattr(obj, "todays_ride_events", None)
        if events is None:
            return []
        return RideEventSerializer(events, many=True).data


class RideWriteSerializer(serializers.ModelSerializer):
    """Write representation: rider and driver by primary key."""

    class Meta:
        model = Ride
        fields = (
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
        )
