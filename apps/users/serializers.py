from rest_framework import serializers

from .models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    """
    Basic serializer to pass CustomUser details to the front end.
    Extend with any fields your app needs.
    """

    avatar_url = serializers.ReadOnlyField()
    get_display_name = serializers.SerializerMethodField()
    username = serializers.CharField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_email_verified = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "avatar_url",
            "get_display_name",
            "language",
            "timezone",
            "date_joined",
            "is_email_verified",
        )

    def get_get_display_name(self, obj: CustomUser) -> str:
        """Get the user's display name"""
        return obj.get_display_name()

    def get_is_email_verified(self, obj: CustomUser) -> bool:
        """Check if user's email is verified"""
        return obj.has_verified_email
