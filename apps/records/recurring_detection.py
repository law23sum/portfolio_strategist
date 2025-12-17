"""
Recurring Transaction Detection Service
Automatically detects recurring transaction patterns
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from .models import (
    FinancialTransaction,
    RecurringTransaction,
)


class RecurringTransactionDetector:
    """Detect recurring transaction patterns"""

    @staticmethod
    def detect_recurring_transactions(user, account=None, min_confidence=60):
        """Detect recurring transactions for a user"""
        detected = []

        # Get transactions
        transactions = FinancialTransaction.objects.filter(account__user=user)
        if account:
            transactions = transactions.filter(account=account)

        # Group by merchant and amount
        patterns = defaultdict(list)

        for transaction in transactions.filter(transaction_type="debit"):
            key = (transaction.merchant_name or transaction.description[:50], transaction.amount)
            patterns[key].append(transaction)

        # Analyze patterns
        for (merchant, amount), trans_list in patterns.items():
            if len(trans_list) < 3:  # Need at least 3 occurrences
                continue

            # Calculate frequency
            trans_list.sort(key=lambda t: t.date)
            dates = [t.date for t in trans_list]

            # Calculate average days between transactions
            intervals = []
            for i in range(1, len(dates)):
                delta = (dates[i] - dates[i - 1]).days
                intervals.append(delta)

            if not intervals:
                continue

            avg_interval = sum(intervals) / len(intervals)

            # Determine frequency
            frequency = RecurringTransactionDetector._determine_frequency(avg_interval)

            # Calculate confidence based on consistency
            interval_variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
            consistency = max(0, 100 - (interval_variance / avg_interval * 100)) if avg_interval > 0 else 0
            confidence = min(100, consistency * (len(trans_list) / 10))  # More occurrences = higher confidence

            if confidence >= min_confidence:
                # Get most recent transaction
                last_trans = max(trans_list, key=lambda t: t.date)

                # Calculate next occurrence
                next_occurrence = last_trans.date + timedelta(days=int(avg_interval))

                # Check if pattern already exists
                existing = RecurringTransaction.objects.filter(
                    user=user, account=last_trans.account, description=merchant, amount=amount, frequency=frequency
                ).first()

                if existing:
                    # Update existing
                    existing.next_occurrence = next_occurrence
                    existing.last_occurrence = last_trans.date
                    existing.confidence_score = Decimal(str(confidence))
                    existing.save()
                    detected.append(existing)
                else:
                    # Create new
                    recurring = RecurringTransaction.objects.create(
                        user=user,
                        account=last_trans.account,
                        description=merchant,
                        amount=amount,
                        category=last_trans.category,
                        merchant_name=merchant,
                        frequency=frequency,
                        next_occurrence=next_occurrence,
                        last_occurrence=last_trans.date,
                        is_detected=True,
                        confidence_score=Decimal(str(confidence)),
                    )
                    # Link matching transactions
                    recurring.matching_transactions.set(trans_list)
                    detected.append(recurring)

        return detected

    @staticmethod
    def _determine_frequency(avg_days):
        """Determine frequency from average days between transactions"""
        if avg_days <= 2:
            return "daily"
        elif avg_days <= 9:
            return "weekly"
        elif avg_days <= 18:
            return "biweekly"
        elif avg_days <= 35:
            return "monthly"
        elif avg_days <= 95:
            return "quarterly"
        else:
            return "yearly"
