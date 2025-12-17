from dj_rest_auth.jwt_auth import CookieTokenRefreshSerializer
from dj_rest_auth.serializers import JWTSerializer, LoginSerializer
from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

User = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    """
    Custom login serializer that accepts both email and username.
    Since the app uses email authentication, we prioritize email but also support username.
    """

    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={"input_type": "password"})

    def validate(self, attrs):
        username = attrs.get("username", "").strip() if attrs.get("username") else ""
        email = attrs.get("email", "").strip() if attrs.get("email") else ""
        password = attrs.get("password")

        if not password:
            raise serializers.ValidationError("Password is required.")

        if not email and not username:
            raise serializers.ValidationError("Either email or username is required.")

        # Try to get user by email first (since that's the primary auth method)
        user = None
        if email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # If multiple users with same email (shouldn't happen), get the first one
                user = User.objects.filter(email__iexact=email).first()

        # If no user found by email, try username
        if not user and username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError("Unable to log in with provided credentials.")

        # Authenticate the user - use the username field for authentication
        authenticated_user = authenticate(
            request=self.context.get("request"), username=user.username, password=password
        )
        if not authenticated_user:
            raise serializers.ValidationError("Unable to log in with provided credentials.")

        attrs["user"] = authenticated_user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    detail = serializers.CharField()
    jwt = JWTSerializer(required=False)
    temp_otp_token = serializers.CharField(required=False)


class PlaidLinkTokenResponseSerializer(serializers.Serializer):
    link_token = serializers.CharField()
    expiration = serializers.CharField()

    class Meta:
        ref_name = "PlaidLinkTokenResponse"


class PlaidPublicTokenExchangeSerializer(serializers.Serializer):
    public_token = serializers.CharField()

    class Meta:
        ref_name = "PlaidPublicTokenExchangeRequest"


class PlaidAuthExchangeResponseSerializer(JWTSerializer):
    status = serializers.CharField()
    detail = serializers.CharField()

    class Meta:
        ref_name = "PlaidAuthExchangeResponse"


class CookieTokenRefreshResponseSerializer(CookieTokenRefreshSerializer):
    class Meta:
        ref_name = "CookieTokenRefreshResponse"


class OtpRequestSerializer(serializers.Serializer):
    temp_otp_token = serializers.CharField()
    otp = serializers.CharField()
