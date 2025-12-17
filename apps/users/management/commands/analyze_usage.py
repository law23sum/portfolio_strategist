from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db.models.functions import ExtractHour, ExtractMonth, ExtractWeekDay, TruncDate
from django.utils import timezone

from apps.users.models import CustomUser


class Command(BaseCommand):
    help = "Analyzes user usage patterns including login times and peak usage periods"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Number of days to analyze (default: 90)",
        )

    def handle(self, *args, **options):
        days = options["days"]
        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        self.stdout.write(self.style.SUCCESS(f"\n=== Usage Analysis (Last {days} days) ===\n"))

        # Get users with login activity
        users_with_logins = CustomUser.objects.exclude(last_login__isnull=True)
        recent_logins = users_with_logins.filter(last_login__gte=cutoff_date)

        total_users = CustomUser.objects.count()
        users_with_logins_count = users_with_logins.count()
        recent_logins_count = recent_logins.count()

        self.stdout.write(f"Total users: {total_users}")
        self.stdout.write(f"Users with login history: {users_with_logins_count}")
        self.stdout.write(f"Users active in last {days} days: {recent_logins_count}")
        self.stdout.write("")

        if recent_logins_count == 0:
            self.stdout.write(self.style.WARNING("No recent login activity found."))
            return

        # Analyze by hour of day
        self.stdout.write(self.style.SUCCESS("=== Usage by Hour of Day ==="))
        hour_stats = (
            recent_logins.annotate(hour=ExtractHour("last_login"))
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("hour")
        )

        hour_data = {item["hour"]: item["count"] for item in hour_stats}
        max_hour_count = max(hour_data.values()) if hour_data else 0

        for hour in range(24):
            count = hour_data.get(hour, 0)
            bar_length = int((count / max_hour_count * 50)) if max_hour_count > 0 else 0
            bar = "█" * bar_length
            hour_label = f"{hour:02d}:00"
            self.stdout.write(f"{hour_label}: {count:4d} {bar}")

        peak_hour = max(hour_data.items(), key=lambda x: x[1]) if hour_data else None
        if peak_hour:
            self.stdout.write(f"\nPeak hour: {peak_hour[0]:02d}:00 ({peak_hour[1]} users)")
        self.stdout.write("")

        # Analyze by day of week
        # Django's ExtractWeekDay: 1=Sunday, 2=Monday, ..., 7=Saturday
        self.stdout.write(self.style.SUCCESS("=== Usage by Day of Week ==="))
        day_names = {1: "Sunday", 2: "Monday", 3: "Tuesday", 4: "Wednesday", 5: "Thursday", 6: "Friday", 7: "Saturday"}

        day_stats = (
            recent_logins.annotate(day_of_week=ExtractWeekDay("last_login"))
            .values("day_of_week")
            .annotate(count=Count("id"))
            .order_by("day_of_week")
        )

        day_data = {item["day_of_week"]: item["count"] for item in day_stats}
        max_day_count = max(day_data.values()) if day_data else 0

        # Display in order: Sunday through Saturday
        for day_num in range(1, 8):
            count = day_data.get(day_num, 0)
            bar_length = int((count / max_day_count * 50)) if max_day_count > 0 else 0
            bar = "█" * bar_length
            day_name = day_names[day_num]
            self.stdout.write(f"{day_name:12s}: {count:4d} {bar}")

        peak_day = max(day_data.items(), key=lambda x: x[1]) if day_data else None
        if peak_day:
            self.stdout.write(f"\nPeak day: {day_names[peak_day[0]]} ({peak_day[1]} users)")
        self.stdout.write("")

        # Analyze by month
        self.stdout.write(self.style.SUCCESS("=== Usage by Month ==="))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        month_stats = (
            recent_logins.annotate(month=ExtractMonth("last_login"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )

        month_data = {item["month"]: item["count"] for item in month_stats}
        max_month_count = max(month_data.values()) if month_data else 0

        for month_num in range(1, 13):
            count = month_data.get(month_num, 0)
            bar_length = int((count / max_month_count * 50)) if max_month_count > 0 else 0
            bar = "█" * bar_length
            month_name = month_names[month_num - 1]
            self.stdout.write(f"{month_name:4s}: {count:4d} {bar}")

        peak_month = max(month_data.items(), key=lambda x: x[1]) if month_data else None
        if peak_month:
            self.stdout.write(f"\nPeak month: {month_names[peak_month[0] - 1]} ({peak_month[1]} users)")
        self.stdout.write("")

        # Daily activity over time
        self.stdout.write(self.style.SUCCESS("=== Daily Activity (Last 30 days) ==="))
        daily_cutoff = timezone.now() - timezone.timedelta(days=30)
        daily_stats = (
            recent_logins.filter(last_login__gte=daily_cutoff)
            .annotate(date=TruncDate("last_login"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        if daily_stats:
            daily_data = {str(item["date"]): item["count"] for item in daily_stats}
            max_daily_count = max(daily_data.values()) if daily_data else 0

            # Show last 30 days
            for i in range(30):
                date = (timezone.now() - timezone.timedelta(days=i)).date()
                date_str = str(date)
                count = daily_data.get(date_str, 0)
                bar_length = int((count / max_daily_count * 30)) if max_daily_count > 0 else 0
                bar = "█" * bar_length
                self.stdout.write(f"{date_str}: {count:4d} {bar}")

            peak_daily = max(daily_data.items(), key=lambda x: x[1]) if daily_data else None
            if peak_daily:
                self.stdout.write(f"\nPeak day: {peak_daily[0]} ({peak_daily[1]} users)")
        self.stdout.write("")

        # Most active users
        self.stdout.write(self.style.SUCCESS("=== Summary ==="))
        self.stdout.write("Most usage time period:")
        if peak_hour:
            self.stdout.write(f"  Hour: {peak_hour[0]:02d}:00 ({peak_hour[1]} users)")
        if peak_day:
            self.stdout.write(f"  Day: {day_names[peak_day[0]]} ({peak_day[1]} users)")
        if peak_month:
            self.stdout.write(f"  Month: {month_names[peak_month[0] - 1]} ({peak_month[1]} users)")

        # Average users per day
        if daily_stats:
            avg_daily = sum(daily_data.values()) / len(daily_data) if daily_data else 0
            self.stdout.write(f"\nAverage active users per day: {avg_daily:.1f}")

        self.stdout.write("")
