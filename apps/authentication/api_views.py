from allauth.mfa.models import Authenticator

try:
    from allauth.mfa.totp.internal.auth import TOTP
except ModuleNotFoundError:  # pragma: no cover - fallback for older allauth versions
    TOTP = None
import logging

from allauth.account.models import EmailAddress
from dj_rest_auth.jwt_auth import get_refresh_view
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.serializers import JWTSerializer
from dj_rest_auth.views import LoginView
from django.core.cache import cache
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from apps.records.plaid_data_distribution import PlaidDataDistributionService
from apps.users.models import CustomUser

from .serializers import (
    CookieTokenRefreshResponseSerializer,
    OtpRequestSerializer,
    PlaidAuthExchangeResponseSerializer,
    PlaidLinkTokenResponseSerializer,
    PlaidPublicTokenExchangeSerializer,
)

logger = logging.getLogger(__name__)


class LoginViewWith2fa(LoginView):
    """
    Custom login view that checks if 2FA is enabled for the user.
    """

    from .serializers import CustomLoginSerializer

    serializer_class = CustomLoginSerializer
    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for login

    def get_permissions(self):
        """
        Explicitly return AllowAny permission to override default permission classes.
        """
        return [AllowAny()]


class RegisterViewWithAllowAny(RegisterView):
    """
    Custom register view that explicitly allows unauthenticated access.
    dj_rest_auth's RegisterView should have AllowAny by default, but we're being explicit
    to ensure it works with our custom permission classes.
    """

    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for registration

    def get_permissions(self):
        """
        Explicitly return AllowAny permission to override default permission classes.
        """
        return [AllowAny()]


class TokenRefreshViewWithAllowAny(TokenRefreshView):
    """
    Custom token refresh view that explicitly allows unauthenticated access.
    Token refresh should work without authentication since it uses the refresh token.
    """

    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token refresh

    def get_permissions(self):
        """Explicitly return AllowAny permission."""
        return [AllowAny()]


class TokenVerifyViewWithAllowAny(TokenVerifyView):
    """
    Custom token verify view that explicitly allows unauthenticated access.
    Token verification should work without authentication since it uses the token itself.
    """

    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token verification

    def get_permissions(self):
        """Explicitly return AllowAny permission."""
        return [AllowAny()]


class TokenObtainPairViewWithAllowAny(TokenObtainPairView):
    """
    Custom token obtain view that explicitly allows unauthenticated access.
    Token obtain should work without authentication since it uses credentials.
    """

    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token obtain

    def get_permissions(self):
        """Explicitly return AllowAny permission."""
        return [AllowAny()]


# For dj_rest_auth refresh view, inherit from the view class returned by get_refresh_view()
# This view handles JWT refresh tokens from dj_rest_auth
_refresh_view_base = get_refresh_view()
if isinstance(_refresh_view_base, type):

    class RefreshTokenViewWithAllowAny(_refresh_view_base):
        """
        Custom dj_rest_auth refresh token view that explicitly allows unauthenticated access.
        """

        permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token refresh
        serializer_class = CookieTokenRefreshResponseSerializer

        def get_permissions(self):
            """Explicitly return AllowAny permission."""
            return [AllowAny()]
else:
    # Fallback: if get_refresh_view() returns something unexpected, use TokenRefreshView
    class RefreshTokenViewWithAllowAny(TokenRefreshView):
        """
        Custom token refresh view (fallback) that explicitly allows unauthenticated access.
        """

        permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token refresh
        serializer_class = CookieTokenRefreshResponseSerializer

        def get_permissions(self):
            """Explicitly return AllowAny permission."""
            return [AllowAny()]


@extend_schema(tags=["api"])
class VerifyOTPView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OtpRequestSerializer

    def get_permissions(self):
        """Explicitly return AllowAny permission."""
        return [AllowAny()]

    @extend_schema(
        responses={200: JWTSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_token = serializer.validated_data["temp_otp_token"]
        otp = serializer.validated_data["otp"]

        if TOTP is None:
            logger.error("TOTP support unavailable in installed django-allauth version.")
            return Response(
                {"status": "mfa_unavailable", "detail": "Time-based one-time passwords are not supported."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        user_id = cache.get(temp_token)
        if not user_id:
            return Response(
                {"status": "token_expired", "detail": "Invalid temporary token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        user = CustomUser.objects.get(id=user_id)
        if user and TOTP(Authenticator.objects.get(user=user, type=Authenticator.Type.TOTP)).validate_code(otp):
            # OTP is valid, generate JWT tokens
            refresh = RefreshToken.for_user(user)
            jwt_data = JWTSerializer(
                {
                    "user": user,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            ).data
            # Also return access and refresh at top level for easier mobile app consumption
            return Response(
                {
                    **jwt_data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                status=status.HTTP_200_OK,
            )
        else:
            # OTP is invalid
            return Response({"status": "invalid_otp", "detail": "Invalid OTP code"}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["api"])
class PlaidAuthLinkTokenView(GenericAPIView):
    """
    Create a Plaid Link token for authentication/login flow.
    """

    permission_classes = [AllowAny]
    serializer_class = PlaidLinkTokenResponseSerializer

    @extend_schema(
        responses=PlaidLinkTokenResponseSerializer,
    )
    def post(self, request):
        try:
            from apps.records.aggregation_service import PlaidAggregationService

            service = PlaidAggregationService()
            link_token_data = service.create_link_token(for_auth=True)

            return Response(link_token_data, status=status.HTTP_200_OK)
        except ImportError as e:
            logger.error(f"Plaid not available: {e}")
            return Response(
                {"error": "Plaid Python SDK not installed. Install with: pip install plaid-python"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"Error creating Plaid auth link token: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["api"])
class PlaidAuthExchangeView(GenericAPIView):
    """
    Exchange Plaid public token for access token and authenticate/create user.
    """

    permission_classes = [AllowAny]
    serializer_class = PlaidPublicTokenExchangeSerializer

    @extend_schema(
        request=PlaidPublicTokenExchangeSerializer,
        responses=PlaidAuthExchangeResponseSerializer,
    )
    def post(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            public_token = serializer.validated_data["public_token"]

            from apps.records.aggregation_service import PlaidAggregationService

            service = PlaidAggregationService()

            # Exchange public token for access token
            access_token = service.exchange_public_token(public_token)

            # Get identity information from Plaid
            identity_data = service.get_identity(access_token)

            # Extract email from identity (use first email found)
            email = None
            if identity_data.get("emails"):
                email = identity_data["emails"][0]

            if not email:
                return Response(
                    {"error": "Could not retrieve email from bank account. Please use email/password login."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Find or create user
            user = None
            try:
                # Try to find user by email
                user = CustomUser.objects.get(email=email)
                # Verify email if not already verified
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user, email=email, defaults={"verified": True}
                )
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
            except CustomUser.DoesNotExist:
                # Create new user
                # Extract name from identity
                name = identity_data.get("names", [""])[0] if identity_data.get("names") else ""
                name_parts = name.split(" ", 1) if name else ["", ""]
                first_name = name_parts[0] if len(name_parts) > 0 else ""
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                # Generate username from email
                username = email.split("@")[0]
                # Ensure username is unique
                base_username = username
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=None,  # No password for Plaid-authenticated users
                )

                # Mark email as verified
                EmailAddress.objects.create(user=user, email=email, verified=True, primary=True)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            jwt_data = JWTSerializer(
                {
                    "user": user,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            ).data

            # Distribute Plaid data so linked pages have immediate access
            try:
                PlaidDataDistributionService.distribute_plaid_data(
                    user=user,
                    access_token=access_token,
                    identity_data=identity_data,
                )
            except Exception as distribution_error:
                logger.warning(
                    "Plaid data distribution failed post-login for user %s: %s",
                    user.id,
                    distribution_error,
                )

            # Also log the user in via Django session for web compatibility
            from django.contrib.auth import login

            login(request, user)

            response_payload = PlaidAuthExchangeResponseSerializer(
                {
                    **jwt_data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "status": "success",
                    "detail": "Authenticated with Plaid successfully",
                }
            ).data

            return Response(response_payload, status=status.HTTP_200_OK)
        except ImportError as e:
            logger.error(f"Plaid not available: {e}")
            return Response(
                {"error": "Plaid Python SDK not installed. Install with: pip install plaid-python"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"Error in Plaid authentication: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
