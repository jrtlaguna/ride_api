from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.api.v1.serializers import AuthTokenResponseSerializer, AuthTokenSerializer


class ObtainAuthTokenView(APIView):
    """Exchange email and password for an API token."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = AuthTokenSerializer

    @extend_schema(
        request=AuthTokenSerializer,
        responses={
            200: AuthTokenResponseSerializer,
            400: OpenApiResponse(description="Invalid credentials."),
        },
        auth=[],
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "id_user": user.id_user,
                "email": user.email,
                "role": user.role,
            }
        )
