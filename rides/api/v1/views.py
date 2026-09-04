from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdminRole
from rides.api.v1.filters import RideEventFilter, RideFilter
from rides.api.v1.serializers import (
    RideEventSerializer,
    RideSerializer,
    RideWriteSerializer,
)
from rides.models import Ride, RideEvent

TODAYS_EVENTS_WINDOW = timedelta(hours=24)


class StableOrderingFilter(OrderingFilter):
    """OrderingFilter that tolerates accepted-but-unimplemented sort keys and
    always breaks ties on the primary key.

    Keys listed in a view's ``ignored_ordering_fields`` are dropped before
    validation, so requesting one is accepted and simply falls back to the
    view's default ordering rather than erroring.

    The primary key is appended because without a total order, LIMIT/OFFSET
    pagination can repeat or skip rows between pages whenever several rows
    share the sort value.
    """

    def remove_invalid_fields(self, queryset, fields, view, request):
        ignored = getattr(view, "ignored_ordering_fields", ())
        fields = [field for field in fields if field.lstrip("-") not in ignored]
        return super().remove_invalid_fields(queryset, fields, view, request)

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        primary_key = queryset.model._meta.pk.name
        if ordering and primary_key not in ordering:
            return list(ordering) + [primary_key]
        return ordering


class RideViewSet(viewsets.ModelViewSet):
    """CRUD for rides. Listing embeds rider, driver and the last 24h of events."""

    permission_classes = (IsAuthenticated, IsAdminRole)
    filter_backends = (DjangoFilterBackend, StableOrderingFilter)
    filterset_class = RideFilter

    ordering_fields = ("pickup_time",)
    # Ride has no created_at column, so the autoincrement pk stands in for
    # creation order. Descending: latest ride first.
    ordering = ("-id_ride",)

    # TODO: accept "distance" as a sort key.
    ignored_ordering_fields = ("distance",)

    lookup_field = "id_ride"

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RideWriteSerializer
        return RideSerializer

    def get_queryset(self):
        queryset = Ride.objects.all()
        if self.action not in ("list", "retrieve"):
            return queryset
        cutoff = timezone.now() - TODAYS_EVENTS_WINDOW
        # select_related folds rider and driver into the ride query; the
        # Prefetch adds exactly one more for every ride on the page, already
        # narrowed to the 24h window. Two queries, plus pagination's COUNT.
        return queryset.select_related("id_rider", "id_driver").prefetch_related(
            Prefetch(
                "ride_events",
                # Latest event first within each ride. Leading with id_ride
                # matches ride_event_ride_dt_idx, so this walks the index
                # rather than sorting.
                queryset=RideEvent.objects.filter(created_at__gte=cutoff).order_by(
                    "id_ride", "-created_at"
                ),
                to_attr="todays_ride_events",
            )
        )


class RideEventViewSet(viewsets.ModelViewSet):
    """CRUD for individual ride events, unconstrained by the 24h window."""

    serializer_class = RideEventSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)
    filter_backends = (DjangoFilterBackend, StableOrderingFilter)
    filterset_class = RideEventFilter
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)
    lookup_field = "id_ride_event"

    def get_queryset(self):
        return RideEvent.objects.select_related("id_ride")
