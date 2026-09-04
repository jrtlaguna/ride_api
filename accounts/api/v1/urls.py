from django.urls import path

from accounts.api.v1.views import ObtainAuthTokenView

app_name = "accounts_v1"

urlpatterns = [path("token/", ObtainAuthTokenView.as_view(), name="token-obtain")]
