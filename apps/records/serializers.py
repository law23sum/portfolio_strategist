from rest_framework import serializers

from .models import BudgetScenario, Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receipt
        fields = ["id", "image", "title", "amount", "date"]


class BudgetScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetScenario
        fields = ["id", "name", "inputs", "results", "created_at", "updated_at"]
