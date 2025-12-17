"""
Notification Generation Service
Automatically generates financial notifications based on user's financial data
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import (
    Bill,
    FinancialCalendarEvent,
    FinancialGoal,
    FinancialNotification,
    FinancialTransaction,
    LinkedAccount,
)


class NotificationGenerator:
    """Generate financial notifications for users"""

    @staticmethod
    def generate_all_notifications(user):
        """Generate all types of notifications for a user"""
        notifications = []

        # Goal-related notifications
        notifications.extend(NotificationGenerator.generate_goal_notifications(user))

        # Account balance notifications
        notifications.extend(NotificationGenerator.generate_balance_notifications(user))

        # Bill due notifications
        notifications.extend(NotificationGenerator.generate_bill_notifications(user))

        # Spending alerts
        notifications.extend(NotificationGenerator.generate_spending_notifications(user))

        # Calendar event reminders
        notifications.extend(NotificationGenerator.generate_calendar_reminders(user))

        return notifications

    @staticmethod
    def generate_goal_notifications(user):
        """Generate notifications for financial goals"""
        notifications = []
        goals = FinancialGoal.objects.filter(user=user, status="active")

        for goal in goals:
            # Goal milestone reached (25%, 50%, 75%, 100%)
            milestones = [25, 50, 75, 100]
            progress = goal.progress_percentage

            for milestone in milestones:
                if milestone - 5 <= progress < milestone + 5:  # Within 5% of milestone
                    # Check if we've already notified for this milestone
                    existing = FinancialNotification.objects.filter(
                        user=user, related_goal=goal, notification_type="goal_milestone", metadata__milestone=milestone
                    ).exists()

                    if not existing:
                        notification = FinancialNotification.objects.create(
                            user=user,
                            notification_type="goal_milestone",
                            title=f"Goal Milestone: {goal.name}",
                            message=f"Congratulations! You've reached {milestone}% of your goal: {goal.name}",
                            priority="medium",
                            related_goal=goal,
                            action_url="/records/goals/",
                            action_label="View Goals",
                            metadata={"milestone": milestone, "progress": progress},
                        )
                        notifications.append(notification)

            # Goal deadline approaching (30 days, 7 days)
            if goal.target_date:
                days_remaining = goal.days_remaining
                if days_remaining and days_remaining <= 30:
                    existing = FinancialNotification.objects.filter(
                        user=user,
                        related_goal=goal,
                        notification_type="goal_deadline",
                        metadata__days_remaining=days_remaining,
                    ).exists()

                    if not existing and days_remaining <= 30:
                        priority = "urgent" if days_remaining <= 7 else "high"
                        notification = FinancialNotification.objects.create(
                            user=user,
                            notification_type="goal_deadline",
                            title=f"Goal Deadline Approaching: {goal.name}",
                            message=f"Your goal '{goal.name}' deadline is in {days_remaining} days. You need ${goal.remaining_amount:.2f} more.",
                            priority=priority,
                            related_goal=goal,
                            action_url="/records/goals/",
                            action_label="View Goal",
                            metadata={"days_remaining": days_remaining},
                        )
                        notifications.append(notification)

            # Goal progress update (monthly)
            last_notification = (
                FinancialNotification.objects.filter(user=user, related_goal=goal, notification_type="goal_progress")
                .order_by("-created_at")
                .first()
            )

            if not last_notification or (timezone.now() - last_notification.created_at).days >= 30:
                notification = FinancialNotification.objects.create(
                    user=user,
                    notification_type="goal_progress",
                    title=f"Goal Progress Update: {goal.name}",
                    message=f"Your goal '{goal.name}' is {goal.progress_percentage:.1f}% complete. ${goal.remaining_amount:.2f} remaining.",
                    priority="low",
                    related_goal=goal,
                    action_url="/records/goals/",
                    action_label="View Goal",
                )
                notifications.append(notification)

        return notifications

    @staticmethod
    def generate_balance_notifications(user):
        """Generate low balance notifications"""
        notifications = []
        accounts = LinkedAccount.objects.filter(user=user, status="active", account_type="depository")

        for account in accounts:
            latest_balance = account.balances.first()
            if latest_balance:
                # Low balance threshold (e.g., below $100 or 10% of typical balance)
                if latest_balance.current_balance < Decimal("100"):
                    # Check if we've notified recently (within 7 days)
                    existing = FinancialNotification.objects.filter(
                        user=user,
                        related_account=account,
                        notification_type="low_balance",
                        created_at__gte=timezone.now() - timedelta(days=7),
                    ).exists()

                    if not existing:
                        notification = FinancialNotification.objects.create(
                            user=user,
                            notification_type="low_balance",
                            title=f"Low Balance Alert: {account.account_name}",
                            message=f"Your {account.account_name} balance is ${latest_balance.current_balance:.2f}",
                            priority="high",
                            related_account=account,
                            action_url=f"/records/account/{account.id}/",
                            action_label="View Account",
                        )
                        notifications.append(notification)

        return notifications

    @staticmethod
    def generate_bill_notifications(user):
        """Generate bill due notifications"""
        notifications = []
        bills = Bill.objects.filter(user=user, is_active=True)

        for bill in bills:
            days_until_due = (bill.next_due_date - timezone.now().date()).days

            if 0 <= days_until_due <= 7:  # Due within 7 days
                existing = FinancialNotification.objects.filter(
                    user=user,
                    notification_type="bill_due",
                    metadata__bill_id=bill.id,
                    created_at__gte=timezone.now() - timedelta(days=1),
                ).exists()

                if not existing:
                    priority = "urgent" if days_until_due <= 1 else "high" if days_until_due <= 3 else "medium"
                    notification = FinancialNotification.objects.create(
                        user=user,
                        notification_type="bill_due",
                        title=f"Bill Due: {bill.name}",
                        message=f"Your bill '{bill.name}' for ${bill.amount:.2f} is due in {days_until_due} days ({bill.next_due_date})",
                        priority=priority,
                        action_url="/records/calendar/",
                        action_label="View Calendar",
                        metadata={
                            "bill_id": bill.id,
                            "amount": str(bill.amount),
                            "due_date": bill.next_due_date.isoformat(),
                        },
                    )
                    notifications.append(notification)

        return notifications

    @staticmethod
    def generate_spending_notifications(user):
        """Generate high spending alerts"""
        notifications = []

        # Check spending in last 7 days
        week_ago = timezone.now().date() - timedelta(days=7)
        recent_spending = FinancialTransaction.objects.filter(
            account__user=user, transaction_type="debit", date__gte=week_ago
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # High spending threshold (e.g., > $1000 in a week)
        if abs(recent_spending) > Decimal("1000"):
            existing = FinancialNotification.objects.filter(
                user=user, notification_type="high_spending", created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()

            if not existing:
                notification = FinancialNotification.objects.create(
                    user=user,
                    notification_type="high_spending",
                    title="High Spending Alert",
                    message=f"You've spent ${abs(recent_spending):.2f} in the last 7 days. Consider reviewing your budget.",
                    priority="medium",
                    action_url="/records/budget-planner/",
                    action_label="View Budget",
                )
                notifications.append(notification)

        # Large transaction alert (> $500)
        large_transactions = FinancialTransaction.objects.filter(
            account__user=user, amount__gte=Decimal("500"), date__gte=timezone.now().date() - timedelta(days=1)
        )

        for transaction in large_transactions:
            existing = FinancialNotification.objects.filter(
                user=user, related_transaction=transaction, notification_type="transaction_large"
            ).exists()

            if not existing:
                notification = FinancialNotification.objects.create(
                    user=user,
                    notification_type="transaction_large",
                    title="Large Transaction Alert",
                    message=f"Large transaction detected: ${transaction.amount:.2f} - {transaction.description[:50]}",
                    priority="medium",
                    related_transaction=transaction,
                    action_url=f"/records/account/{transaction.account.id}/",
                    action_label="View Transaction",
                )
                notifications.append(notification)

        return notifications

    @staticmethod
    def generate_calendar_reminders(user):
        """Generate calendar event reminders"""
        notifications = []
        tomorrow = timezone.now().date() + timedelta(days=1)

        upcoming_events = FinancialCalendarEvent.objects.filter(
            user=user, reminder_date__lte=tomorrow, is_completed=False
        )

        for event in upcoming_events:
            existing = FinancialNotification.objects.filter(
                user=user,
                notification_type="payment_reminder",
                metadata__event_id=event.id,
                created_at__gte=timezone.now() - timedelta(days=1),
            ).exists()

            if not existing:
                notification = FinancialNotification.objects.create(
                    user=user,
                    notification_type="payment_reminder",
                    title=f"Reminder: {event.title}",
                    message=f"Reminder: {event.description or event.title} on {event.event_date}",
                    priority="medium",
                    action_url="/records/calendar/",
                    action_label="View Calendar",
                    metadata={"event_id": event.id},
                )
                notifications.append(notification)

        return notifications
