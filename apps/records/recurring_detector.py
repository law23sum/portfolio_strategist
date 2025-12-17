"""
Recurring Transaction Detection Service
Detects patterns in transactions to identify recurring payments
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import (
    FinancialTransaction,
    RecurringTransaction,
)


class RecurringTransactionDetector:
    """Detect recurring transaction patterns"""

    MIN_OCCURRENCES = 3  # Minimum number of occurrences to consider it recurring
    AMOUNT_TOLERANCE = 0.05  # 5% tolerance for amount matching
    DAY_TOLERANCE = 3  # Days tolerance for date matching

    @staticmethod
    def detect_recurring_transactions(user, account=None, min_confidence=60):
        """
        Detect recurring transactions for a user

        Args:
            user: User object
            account: Optional LinkedAccount to filter by
            min_confidence: Minimum confidence score (0-100)

        Returns:
            List of created RecurringTransaction objects
        """
        # Get transactions from last 6 months
        six_months_ago = timezone.now().date() - timedelta(days=180)

        transactions = FinancialTransaction.objects.filter(
            account__user=user, transaction_type="debit", date__gte=six_months_ago
        )

        if account:
            transactions = transactions.filter(account=account)

        # Group by merchant/description
        grouped = defaultdict(list)
        for transaction in transactions:
            key = RecurringTransactionDetector._get_grouping_key(transaction)
            grouped[key].append(transaction)

        detected = []

        # Analyze each group
        for key, transaction_list in grouped.items():
            if len(transaction_list) >= RecurringTransactionDetector.MIN_OCCURRENCES:
                pattern = RecurringTransactionDetector._analyze_pattern(transaction_list)

                if pattern and pattern["confidence"] >= min_confidence:
                    # Create or update recurring transaction
                    rt = RecurringTransactionDetector._create_recurring_transaction(user, transaction_list[0], pattern)
                    if rt:
                        detected.append(rt)

        return detected

    @staticmethod
    def _get_grouping_key(transaction):
        """Create a grouping key for similar transactions"""
        # Normalize merchant name and description
        merchant = (transaction.merchant_name or "").lower().strip()
        description = (transaction.description or "").lower().strip()

        # Use merchant name if available, otherwise use first few words of description
        if merchant:
            key = merchant
        else:
            # Take first 3 words of description
            words = description.split()[:3]
            key = " ".join(words)

        return key

    @staticmethod
    def _analyze_pattern(transactions):
        """Analyze if transactions form a recurring pattern"""
        if len(transactions) < RecurringTransactionDetector.MIN_OCCURRENCES:
            return None

        # Sort by date
        transactions = sorted(transactions, key=lambda t: t.date)

        # Check amount consistency
        amounts = [abs(t.amount) for t in transactions]
        avg_amount = sum(amounts) / len(amounts)

        # Check if amounts are similar (within tolerance)
        amount_variance = sum(abs(a - avg_amount) / avg_amount for a in amounts) / len(amounts)
        if amount_variance > RecurringTransactionDetector.AMOUNT_TOLERANCE:
            return None  # Amounts too variable

        # Analyze frequency
        dates = [t.date for t in transactions]
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i - 1]).days
            intervals.append(interval)

        if not intervals:
            return None

        avg_interval = sum(intervals) / len(intervals)

        # Determine frequency
        frequency = RecurringTransactionDetector._determine_frequency(avg_interval)

        # Calculate confidence based on consistency
        interval_variance = sum(abs(i - avg_interval) for i in intervals) / len(intervals) if intervals else 0
        consistency_score = max(0, 100 - (interval_variance / avg_interval * 100)) if avg_interval > 0 else 0

        # Confidence based on number of occurrences and consistency
        occurrence_score = min(100, (len(transactions) / 6) * 100)  # Max at 6+ occurrences
        confidence = (consistency_score * 0.7) + (occurrence_score * 0.3)

        # Calculate next occurrence
        last_date = max(dates)
        next_occurrence = last_date + timedelta(days=int(avg_interval))

        return {
            "frequency": frequency,
            "amount": avg_amount,
            "confidence": confidence,
            "next_occurrence": next_occurrence,
            "last_occurrence": last_date,
            "interval_days": int(avg_interval),
        }

    @staticmethod
    def _determine_frequency(avg_interval_days):
        """Determine frequency from average interval"""
        if avg_interval_days <= 2:
            return "daily"
        elif avg_interval_days <= 9:
            return "weekly"
        elif avg_interval_days <= 18:
            return "biweekly"
        elif avg_interval_days <= 35:
            return "monthly"
        elif avg_interval_days <= 95:
            return "quarterly"
        elif avg_interval_days <= 370:
            return "yearly"
        else:
            return "custom"

    @staticmethod
    def _create_recurring_transaction(user, sample_transaction, pattern):
        """Create a RecurringTransaction from detected pattern"""
        # Check if similar recurring transaction already exists
        existing = RecurringTransaction.objects.filter(
            user=user,
            account=sample_transaction.account,
            description__icontains=sample_transaction.merchant_name or sample_transaction.description[:50],
            frequency=pattern["frequency"],
        ).first()

        if existing:
            # Update existing
            existing.amount = Decimal(str(pattern["amount"]))
            existing.next_occurrence = pattern["next_occurrence"]
            existing.last_occurrence = pattern["last_occurrence"]
            existing.confidence_score = Decimal(str(pattern["confidence"]))
            existing.save()
            return existing

        # Create new
        rt = RecurringTransaction.objects.create(
            user=user,
            account=sample_transaction.account,
            description=sample_transaction.merchant_name or sample_transaction.description[:255],
            amount=Decimal(str(pattern["amount"])),
            category=sample_transaction.category,
            merchant_name=sample_transaction.merchant_name,
            frequency=pattern["frequency"],
            next_occurrence=pattern["next_occurrence"],
            last_occurrence=pattern["last_occurrence"],
            is_detected=True,
            confidence_score=Decimal(str(pattern["confidence"])),
        )

        # Link matching transactions
        matching_transactions = FinancialTransaction.objects.filter(
            account=sample_transaction.account, date__gte=sample_transaction.date - timedelta(days=180)
        ).filter(
            Q(merchant_name=sample_transaction.merchant_name)
            | Q(description__icontains=sample_transaction.merchant_name or sample_transaction.description[:50])
        )

        rt.matching_transactions.set(matching_transactions[:10])  # Limit to 10

        return rt
