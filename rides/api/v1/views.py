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


class RideViewSet(viewsets.ModelViewSet):
    """CRUD for rides. Listing embeds rider, driver and the last 24h of events."""

    permission_classes = (IsAuthenticated, IsAdminRole)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RideFilter
    ordering_fields = ("pickup_time",)
    # id_ride breaks ties deterministically. Without a total order, LIMIT /
    # OFFSET pagination can repeat or skip rows between pages.
    ordering = ("-pickup_time", "id_ride")
    # The primary key is id_ride, not id: naming it here keeps the URL and the
    # generated schema in agreement about the parameter's name and type.
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
                queryset=RideEvent.objects.filter(created_at__gte=cutoff),
                to_attr="todays_ride_events",
            )
        )


class RideEventViewSet(viewsets.ModelViewSet):
    """CRUD for individual ride events, unconstrained by the 24h window."""

    serializer_class = RideEventSerializer
    permission_classes = (IsAuthenticated, IsAdminRole)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_class = RideEventFilter
    ordering_fields = ("created_at",)
    ordering = ("-created_at", "id_ride_event")
    lookup_field = "id_ride_event"

    def get_queryset(self):
        return RideEvent.objects.select_related("id_ride")
