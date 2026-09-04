import django_filters

from rides.models import Ride, RideEvent


class RideFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Ride.Status.choices)
    rider_email = django_filters.CharFilter(
        field_name="id_rider__email", lookup_expr="iexact"
    )

    class Meta:
        model = Ride
        fields = ("status", "rider_email")


class RideEventFilter(django_filters.FilterSet):
    id_ride = django_filters.NumberFilter(field_name="id_ride__id_ride")
    created_after = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )
    created_before = django_filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = RideEvent
        fields = ("id_ride", "created_after", "created_before")
