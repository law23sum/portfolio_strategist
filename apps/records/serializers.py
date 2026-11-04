from rest_framework import serializers
from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ['id', 'image', 'title', 'amount', 'date', 'user']
        read_only_fields = ['user']  # set by the view from request.user
