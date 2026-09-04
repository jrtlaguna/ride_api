from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.forms import BaseInlineFormSet
from django.utils import timezone

from rides.models import Ride, RideEvent

RECENT_EVENT_WINDOW = timedelta(hours=24)


class RecentRideEventFormSet(BaseInlineFormSet):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(created_at__gte=timezone.now() - RECENT_EVENT_WINDOW)
        )


class RideEventInline(admin.TabularInline):
    model = RideEvent
    formset = RecentRideEventFormSet
    fk_name = "id_ride"
    extra = 0
    fields = ("description", "created_at")
    ordering = ("-created_at",)
    show_change_link = True
    verbose_name_plural = "Ride events (last 24 hours)"


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        "id_ride",
        "status",
        "rider_email",
        "driver_email",
        "pickup_time",
        "event_count",
    )
    list_filter = ("status", "pickup_time")
    date_hierarchy = "pickup_time"
    ordering = ("-pickup_time",)
    search_fields = (
        "id_rider__email",
        "id_driver__email",
        "id_rider__first_name",
        "id_driver__first_name",
    )
    autocomplete_fields = ("id_rider", "id_driver")
    list_select_related = ("id_rider", "id_driver")
    show_full_result_count = False
    inlines = [RideEventInline]

    fieldsets = (
        (None, {"fields": ("status", "id_rider", "id_driver", "pickup_time")}),
        (
            "Pickup location",
            {"fields": ("pickup_latitude", "pickup_longitude")},
        ),
        (
            "Dropoff location",
            {"fields": ("dropoff_latitude", "dropoff_longitude")},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_event_count=Count("ride_events"))

    @admin.display(ordering="id_rider__email", description="Rider")
    def rider_email(self, obj):
        return obj.id_rider.email

    @admin.display(ordering="id_driver__email", description="Driver")
    def driver_email(self, obj):
        return obj.id_driver.email

    @admin.display(ordering="_event_count", description="Events")
    def event_count(self, obj):
        return obj._event_count


@admin.register(RideEvent)
class RideEventAdmin(admin.ModelAdmin):
    list_display = ("id_ride_event", "id_ride", "description", "created_at")
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    search_fields = ("description",)
    autocomplete_fields = ("id_ride",)
    list_select_related = ("id_ride",)
    show_full_result_count = False
