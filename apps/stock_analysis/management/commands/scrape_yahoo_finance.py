"""
Management command to scrape comprehensive Yahoo Finance data for stock symbols.

Usage:
    python manage.py scrape_yahoo_finance AAPL MSFT GOOGL
    python manage.py scrape_yahoo_finance --all  # Scrape all watchlist symbols
    python manage.py scrape_yahoo_finance --symbol AAPL --force
"""

from django.core.management.base import BaseCommand, CommandError

from apps.stock_analysis.models import StockWatchlistEntry
from apps.stock_analysis.tasks import scrape_yahoo_finance_comprehensive


class Command(BaseCommand):
    help = "Scrape comprehensive Yahoo Finance data for stock symbols"

    def add_arguments(self, parser):
        parser.add_argument(
            "symbols",
            nargs="*",
            help="Stock symbols to scrape (e.g., AAPL MSFT GOOGL)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Scrape all symbols in watchlist",
        )
        parser.add_argument(
            "--symbol",
            type=str,
            help="Single symbol to scrape (alternative to positional arguments)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh even if recent data exists",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            dest="async_task",
            help="Run asynchronously via Celery (default: synchronous)",
        )

    def handle(self, *args, **options):
        symbols = options.get("symbols", [])
        symbol_arg = options.get("symbol")
        scrape_all = options.get("all", False)
        force = options.get("force", False)
        async_task = options.get("async_task", False)

        # Determine which symbols to scrape
        if scrape_all:
            symbols = list(StockWatchlistEntry.objects.values_list("symbol", flat=True).distinct())
            if not symbols:
                self.stdout.write(
                    self.style.WARNING("No symbols found in watchlist. Use --symbol or provide symbols as arguments.")
                )
                return
        elif symbol_arg:
            symbols = [symbol_arg]
        elif not symbols:
            raise CommandError(
                "Please provide symbols to scrape, use --symbol SYMBOL, or use --all to scrape all watchlist symbols."
            )

        # Normalize symbols
        symbols = [s.upper().strip() for s in symbols if s]

        if not symbols:
            raise CommandError("No valid symbols provided.")

        self.stdout.write(
            self.style.SUCCESS(f"Starting comprehensive Yahoo Finance scrape for {len(symbols)} symbol(s)...")
        )

        if async_task:
            # Run asynchronously via Celery
            self.stdout.write(self.style.WARNING("Running asynchronously via Celery..."))
            for symbol in symbols:
                try:
                    task = scrape_yahoo_finance_comprehensive.delay(symbol, force_refresh=force)
                    self.stdout.write(self.style.SUCCESS(f"Queued task for {symbol} (task ID: {task.id})"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to queue task for {symbol}: {e}"))
        else:
            # Run synchronously
            successful = 0
            failed = 0

            for symbol in symbols:
                try:
                    self.stdout.write(f"Scraping {symbol}...")
                    result = scrape_yahoo_finance_comprehensive(symbol, force_refresh=force)

                    if result.get("success"):
                        successful += 1
                        price = result.get("current_price")
                        price_str = f"${price:.2f}" if price else "N/A"
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ {symbol}: Success - Price: {price_str}, "
                                f"News: {result.get('news_count', 0)}, "
                                f"Statistics: {result.get('statistics_count', 0)}"
                            )
                        )
                    else:
                        failed += 1
                        error = result.get("error", "Unknown error")
                        self.stdout.write(self.style.ERROR(f"✗ {symbol}: Failed - {error}"))
                except Exception as e:
                    failed += 1
                    self.stdout.write(self.style.ERROR(f"✗ {symbol}: Exception - {str(e)}"))

            # Summary
            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS(f"Completed: {successful} successful, {failed} failed out of {len(symbols)} total")
            )
