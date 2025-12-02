import json
import uuid

from allauth.mfa.models import Authenticator
from allauth.mfa.totp.internal.auth import TOTP
from allauth.mfa.utils import is_mfa_enabled
from dj_rest_auth.serializers import JWTSerializer
from dj_rest_auth.views import LoginView
from django.core.cache import cache
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, Token

from apps.users.models import CustomUser
from allauth.account.models import EmailAddress

from .serializers import LoginResponseSerializer, OtpRequestSerializer

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.http import JsonResponse
from django.contrib.auth import authenticate
import json
import logging

logger = logging.getLogger(__name__)


class LoginViewWith2fa(LoginView):
    """
    Custom login view that checks if 2FA is enabled for the user.
    """
    from .serializers import CustomLoginSerializer
    serializer_class = CustomLoginSerializer

    @extend_schema(
        responses={
            status.HTTP_200_OK: LoginResponseSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.user = serializer.validated_data["user"]
        if is_mfa_enabled(self.user, [Authenticator.Type.TOTP]):
            # Generate a temporary token and store it with the user object
            temp_token = str(uuid.uuid4())
            cache.set(temp_token, self.user.id, timeout=300)  # set a token that will be valid for 5 minutes
            api_auth_serializer = LoginResponseSerializer(
                data={
                    "status": "otp_required",
                    "detail": "OTP required for 2FA",
                    "temp_otp_token": temp_token,
                }
            )
            api_auth_serializer.is_valid(raise_exception=True)
            # use a different status code to make it easier for API clients to handle this case
            return Response(api_auth_serializer.data, status=200)
        else:
            # No 2FA required, generate JWT tokens directly
            from dj_rest_auth.serializers import JWTSerializer
            refresh = RefreshToken.for_user(self.user)
            jwt_data = JWTSerializer(
                {
                    "user": self.user,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            ).data
            # Wrap in our response format
            wrapped_jwt_data = {
                "status": "success",
                "detail": "User logged in.",
                "jwt": jwt_data,
            }
            return Response(wrapped_jwt_data, status=200)


@extend_schema(tags=["api"])
class VerifyOTPView(GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = OtpRequestSerializer

    @extend_schema(
        responses={200: JWTSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        temp_token = serializer.validated_data["temp_otp_token"]
        otp = serializer.validated_data["otp"]

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

    @extend_schema(
        responses={200: {"type": "object", "properties": {"link_token": {"type": "string"}, "expiration": {"type": "string"}}}},
    )
    def post(self, request):
        try:
            from apps.records.aggregation_service import PlaidAggregationService
            from apps.web.meta import absolute_url
            
            service = PlaidAggregationService()
            # Don't include redirect_uri in initial link token creation
            # OAuth redirects will be handled via receivedRedirectUri in the frontend
            # redirect_uri must be whitelisted in Plaid dashboard, so we omit it here
            link_token_data = service.create_link_token(
                for_auth=True,
                redirect_uri=None  # Omit redirect_uri to avoid 400 error
            )
            
            return Response(link_token_data, status=status.HTTP_200_OK)
        except ImportError as e:
            logger.error(f"Plaid not available: {e}")
            return Response(
                {"error": "Plaid Python SDK not installed. Install with: pip install plaid-python"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error creating Plaid auth link token: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["api"])
class PlaidAuthExchangeView(GenericAPIView):
    """
    Exchange Plaid public token for access token and authenticate/create user.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: JWTSerializer},
    )
    def post(self, request):
        try:
            public_token = request.data.get('public_token')
            if not public_token:
                return Response(
                    {"error": "public_token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from apps.records.aggregation_service import PlaidAggregationService
            
            service = PlaidAggregationService()
            
            # Exchange public token for access token
            access_token = service.exchange_public_token(public_token)
            
            # Get identity information from Plaid
            identity_data = service.get_identity(access_token)
            
            # Extract email from identity (use first email found)
            email = None
            if identity_data.get('emails'):
                email = identity_data['emails'][0]
            
            if not email:
                return Response(
                    {"error": "Could not retrieve email from bank account. Please use email/password login."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find or create user
            user = None
            try:
                # Try to find user by email
                user = CustomUser.objects.get(email=email)
                # Verify email if not already verified
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={'verified': True}
                )
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
            except CustomUser.DoesNotExist:
                # Create new user
                # Extract name from identity
                name = identity_data.get('names', [''])[0] if identity_data.get('names') else ''
                name_parts = name.split(' ', 1) if name else ['', '']
                first_name = name_parts[0] if len(name_parts) > 0 else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                # Generate username from email
                username = email.split('@')[0]
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
                    password=None  # No password for Plaid-authenticated users
                )
                
                # Mark email as verified
                EmailAddress.objects.create(
                    user=user,
                    email=email,
                    verified=True,
                    primary=True
                )
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            jwt_data = JWTSerializer(
                {
                    "user": user,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            ).data
            
            # Fetch and save accounts from Plaid
            try:
                # Get institution info from metadata if available
                institution_id = request.data.get('institution_id', '')
                institution_name = request.data.get('institution_name', 'Unknown Institution')
                
                # Fetch accounts
                accounts_data = service._fetch_accounts(access_token)
                item_id = service.get_item_id(access_token)
                
                # Get or create provider
                from apps.records.models import AggregationProvider
                provider, _ = AggregationProvider.objects.get_or_create(
                    name='plaid',
                    defaults={
                        'display_name': 'Plaid',
                        'is_active': True,
                        'environment': 'sandbox'
                    }
                )
                
                # Create linked accounts for each account returned
                from apps.records.models import LinkedAccount, AccountBalance
                from apps.records.encryption import encrypt_token
                from decimal import Decimal
                
                for account_data in accounts_data:
                    # Map Plaid account type to our account type
                    plaid_type = account_data.get('type', '')
                    account_subtype = account_data.get('subtype', '')
                    
                    # Determine account type
                    if plaid_type == 'depository':
                        if account_subtype in ['401a', '401k', '403b', '457b', '529', 'ira', 'keogh', 'pension', 'profit sharing plan', 'retirement', 'roth', 'roth 401k', 'sep ira', 'simple ira', 'sipp', 'thrift savings plan']:
                            account_type = 'retirement'
                        else:
                            account_type = 'depository'
                    elif plaid_type == 'investment':
                        if account_subtype in ['401a', '401k', '403b', '457b', '529', 'ira', 'keogh', 'pension', 'profit sharing plan', 'retirement', 'roth', 'roth 401k', 'sep ira', 'simple ira', 'sipp', 'thrift savings plan']:
                            account_type = 'retirement'
                        elif account_subtype in ['brokerage', 'cash management account', 'money market']:
                            account_type = 'brokerage'
                        else:
                            account_type = 'investment'
                    elif plaid_type == 'credit':
                        account_type = 'credit'
                    elif plaid_type == 'loan':
                        account_type = 'loan'
                    else:
                        account_type = 'other'
                    
                    # Create or update linked account
                    linked_account, created = LinkedAccount.objects.update_or_create(
                        user=user,
                        provider=provider,
                        provider_account_id=account_data.get('account_id'),
                        defaults={
                            'provider_item_id': item_id,
                            'access_token': encrypt_token(access_token),
                            'institution_name': institution_name,
                            'institution_id': institution_id,
                            'account_name': account_data.get('name', 'Unknown Account'),
                            'account_type': account_type,
                            'account_subtype': account_subtype,
                            'account_number_masked': account_data.get('mask', ''),
                            'status': 'active',
                            'metadata': account_data,
                        }
                    )
                    
                    # Save account balance
                    balances = account_data.get('balances', {})
                    if balances:
                        AccountBalance.objects.create(
                            account=linked_account,
                            balance_date=timezone.now(),
                            current_balance=Decimal(str(balances.get('current', 0))),
                            available_balance=Decimal(str(balances.get('available', 0))) if balances.get('available') is not None else None,
                            limit=Decimal(str(balances.get('limit', 0))) if balances.get('limit') is not None else None,
                            currency_code=balances.get('iso_currency_code', 'USD'),
                            raw_data=account_data,
                        )
            except Exception as e:
                logger.error(f"Error saving Plaid accounts: {e}", exc_info=True)
                # Don't fail authentication if account saving fails
            
            # Also log the user in via Django session for web compatibility
            from django.contrib.auth import login
            login(request, user)
            
            return Response(
                {
                    **jwt_data,
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "status": "success",
                    "detail": "Authenticated with Plaid successfully",
                },
                status=status.HTTP_200_OK,
            )
        except ImportError as e:
            logger.error(f"Plaid not available: {e}")
            return Response(
                {"error": "Plaid Python SDK not installed. Install with: pip install plaid-python"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            logger.error(f"Error in Plaid authentication: {e}", exc_info=True)
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["api"])
class PlaidAuthOAuthCallbackView(GenericAPIView):
    """
    OAuth callback endpoint for Plaid Link authentication flow.
    This handles the redirect from banks that use OAuth flow.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        oauth_state_id = request.GET.get('oauth_state_id')
        
        if not oauth_state_id:
            return Response(
                {"error": "Missing oauth_state_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return the OAuth state ID to the frontend so Plaid Link can complete the flow
        return Response({
            "oauth_state_id": oauth_state_id,
            "status": "oauth_callback_received"
        })