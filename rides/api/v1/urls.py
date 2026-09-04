from rest_framework.routers import DefaultRouter

from rides.api.v1.views import RideEventViewSet, RideViewSet

app_name = "rides_v1"

router = DefaultRouter()
router.register("rides", RideViewSet, basename="ride")
router.register("ride-events", RideEventViewSet, basename="ride-event")

urlpatterns = router.urls
