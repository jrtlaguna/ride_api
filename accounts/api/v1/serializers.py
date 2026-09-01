from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class AuthTokenSerializer(serializers.Serializer):
    """Credentials for token retrieval."""

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(
        style={"input_type": "password"}, trim_whitespace=False, write_only=True
    )

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                _("Unable to log in with the provided credentials."),
                code="authorization",
            )
        attrs["user"] = user
        return attrs


class AuthTokenResponseSerializer(serializers.Serializer):
    """Shape of a successful token response. Used for the schema only."""

    token = serializers.CharField()
    id_user = serializers.IntegerField()
    email = serializers.EmailField()
    role = serializers.CharField()
