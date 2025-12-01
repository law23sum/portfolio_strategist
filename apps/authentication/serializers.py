from dj_rest_auth.serializers import JWTSerializer, LoginSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomLoginSerializer(LoginSerializer):
    """
    Custom login serializer that accepts both email and username.
    Since the app uses email authentication, we prioritize email but also support username.
    """
    username = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')

        if not password:
            raise serializers.ValidationError('Password is required.')

        # Try to get user by email first (since that's the primary auth method)
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
        
        # If no user found by email, try username
        if not user and username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials.')

        # Authenticate the user
        user = authenticate(request=self.context.get('request'), username=user.username, password=password)
        if not user:
            raise serializers.ValidationError('Unable to log in with provided credentials.')

        attrs['user'] = user
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    detail = serializers.CharField()
    jwt = JWTSerializer(required=False)
    temp_otp_token = serializers.CharField(required=False)


class OtpRequestSerializer(serializers.Serializer):
    temp_otp_token = serializers.CharField()
    otp = serializers.CharField()
