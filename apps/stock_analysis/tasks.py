"""Celery tasks for refreshing watchlist data via Yahoo Finance scraping."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, List, Tuple, Optional

from celery import shared_task
from django.utils import timezone

from .models import StockWatchlistEntry, StockWatchSnapshot

logger = logging.getLogger(__name__)


def _clean_decimal(value) -> Decimal | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _normalize_news_items(raw_items: List[Dict]) -> List[Dict]:
    normalized = []
    for item in raw_items[:10]:
        # Handle nested structure where data is inside 'summary' object
        # (Yahoo Finance API sometimes returns this structure)
        if item.get("summary") and isinstance(item.get("summary"), dict):
            summary = item.get("summary", {})
            title = summary.get("title") or item.get("title")
            # Try multiple URL sources from nested structure
            url = (
                summary.get("canonicalUrl", {}).get("url") or
                summary.get("clickThroughUrl", {}).get("url") or
                summary.get("previewUrl") or
                item.get("link") or
                item.get("url")
            )
            publisher = (
                summary.get("provider", {}).get("displayName") or
                summary.get("provider", {}).get("name") or
                item.get("publisher") or
                item.get("source")
            )
            summary_text = summary.get("summary") or summary.get("description") or item.get("summary") or item.get("content")
            published = (
                summary.get("pubDate") or
                summary.get("displayTime") or
                item.get("providerPublishTime") or
                item.get("publishedAt")
            )
        else:
            # Handle flat structure (original format)
            title = item.get("title")
            url = item.get("link") or item.get("url")
            publisher = item.get("publisher") or item.get("source")
            summary_text = item.get("summary") or item.get("content")
            published = item.get("providerPublishTime") or item.get("publishedAt")
        
        # Only include items with both title and URL
        if title and url:
            normalized.append(
                {
                    "title": title,
                    "publisher": publisher or "Yahoo Finance",
                    "link": url,
                    "url": url,  # Include both for compatibility
                    "summary": summary_text,
                    "published": published,
                }
            )
    return normalized


def _fetch_symbol_payload(symbol: str) -> Tuple[Dict, List[Dict]]:
    import yfinance as yf

    ticker = yf.Ticker(symbol)

    info = {}
    try:
        info = ticker.get_info() or {}
    except Exception as exc:  # pragma: no cover - yfinance quirks
        logger.warning("yfinance.get_info failed for %s: %s", symbol, exc)

    fast_info = {}
    try:
        fast_info = dict(getattr(ticker, "fast_info", {}) or {})
    except Exception:
        fast_info = {}

    payload = {
        key: info.get(key)
        for key in [
            "shortName",
            "longName",
            "sector",
            "industry",
            "marketCap",
            "trailingPE",
            "forwardPE",
            "dividendYield",
            "beta",
            "regularMarketPrice",
            "regularMarketChangePercent",
            "fiftyTwoWeekHigh",
            "fiftyTwoWeekLow",
            "longBusinessSummary",
        ]
        if key in info
    }
    payload["fast"] = {
        key: fast_info.get(key)
        for key in [
            "lastPrice",
            "lastPriceTime",
            "yearHigh",
            "yearLow",
            "tenDayAverageVolume",
        ]
        if key in fast_info
    }

    news = []
    try:
        news = ticker.news or []
    except Exception as exc:
        logger.warning("yfinance.news failed for %s: %s", symbol, exc)

    return payload, _normalize_news_items(news)


def _resolve_price(payload: Dict) -> Tuple[Decimal | None, Decimal | None]:
    price_sources = [
        payload.get("regularMarketPrice"),
        payload.get("fast", {}).get("lastPrice"),
    ]
    for candidate in price_sources:
        price = _clean_decimal(candidate)
        if price is not None:
            break
    else:
        price = None

    change = payload.get("regularMarketChangePercent")
    if change is None:
        change = payload.get("fast", {}).get("lastChangePercent")
    return price, _clean_decimal(change)


def _refresh_symbol(symbol: str) -> None:
    symbol = symbol.upper()
    if not StockWatchlistEntry.objects.filter(symbol=symbol).exists():
        return

    try:
        payload, news_items = _fetch_symbol_payload(symbol)
    except Exception as exc:  # pragma: no cover - external dependency
        logger.exception("Failed scraping %s", symbol)
        StockWatchSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                "last_error": str(exc),
                "fetched_at": timezone.now(),
            },
        )
        return

    price, change = _resolve_price(payload)
    # NOTE: StockWatchSnapshot stores PUBLIC stock data accessible to ALL users
    snapshot, _ = StockWatchSnapshot.objects.update_or_create(
        symbol=symbol,
        defaults={
            "payload": payload,
            "news_items": news_items,
            "current_price": price,
            "change_percent": change,
            "fetched_at": timezone.now(),
            "last_error": "",
        },
    )

    StockWatchlistEntry.objects.filter(symbol=symbol).update(
        snapshot=snapshot,
        last_refreshed=timezone.now(),
    )


@shared_task
def refresh_watchlist_symbol(symbol: str) -> None:
    """Refresh a single watchlist symbol on demand."""
    _refresh_symbol(symbol)


@shared_task
def refresh_watchlist_snapshots() -> None:
    """Refresh all tracked symbols in the background."""
    symbols = (
        StockWatchlistEntry.objects.values_list("symbol", flat=True).distinct()
    )
    for symbol in symbols:
        _refresh_symbol(symbol)


@shared_task
def scrape_yahoo_finance_comprehensive(symbol: str, force_refresh: bool = False) -> Dict:
    """
    Comprehensive Yahoo Finance scraping task that fetches ALL available details.
    
    This task uses Selenium to scrape Yahoo Finance and fetches:
    - Summary (price, market cap, volume, beta, PE ratio, EPS, dividend yield, 52-week range)
    - Statistics (valuation measures, stock statistics, financial highlights)
    - Chart details (available chart types, historical data)
    - News (all available news articles)
    - Options (calls and puts)
    - Holders (institutional and mutual fund holders)
    - Profile (company description, executives)
    
    Args:
        symbol: Stock symbol to scrape (e.g., 'AAPL', 'MSFT')
        force_refresh: If True, refresh even if recent data exists
    
    Returns:
        Dictionary with success status and data summary
    """
    symbol = symbol.upper().strip()
    logger.info(f"Starting comprehensive Yahoo Finance scrape for {symbol}")
    
    try:
        from .lib.stock_fetcher import StockFetcher
        
        fetcher = StockFetcher()
        
        # Fetch comprehensive Yahoo Finance data
        comprehensive_data = fetcher.fetch_yahoo_finance_comprehensive(symbol)
        
        if not comprehensive_data:
            error_msg = f"No data returned from Yahoo Finance for {symbol}"
            logger.warning(error_msg)
            StockWatchSnapshot.objects.update_or_create(
                symbol=symbol,
                defaults={
                    "last_error": error_msg,
                    "fetched_at": timezone.now(),
                },
            )
            return {
                "success": False,
                "symbol": symbol,
                "error": error_msg,
            }
        
        # Extract summary data for quick access
        summary = comprehensive_data.get('summary', {})
        news_items = comprehensive_data.get('news', [])
        
        # Resolve current price from multiple sources
        current_price = None
        price_sources = [
            summary.get('currentPrice'),
            comprehensive_data.get('statistics', {}).get('Current Price'),
            comprehensive_data.get('statistics', {}).get('Previous Close'),
        ]
        
        for candidate in price_sources:
            if candidate is not None:
                try:
                    # Clean price string (remove $, commas, etc.)
                    if isinstance(candidate, str):
                        candidate = candidate.replace('$', '').replace(',', '').strip()
                    current_price = _clean_decimal(candidate)
                    if current_price is not None:
                        break
                except Exception:
                    continue
        
        # Calculate change percent if available
        change_percent = None
        if summary.get('changePercent'):
            change_percent = _clean_decimal(summary.get('changePercent'))
        
        # Build comprehensive payload with ALL data sections scraped from Yahoo Finance
        # This includes EVERYTHING we can fetch from the website
        # All URLs are scraped: quote, news, chart, key-statistics, history, financials, 
        # balance-sheet, cash-flow, analysis, options, holders
        payload = {
            'summary': summary,
            'statistics': comprehensive_data.get('statistics', {}),
            'chart_details': comprehensive_data.get('chart_details', {}),
            'options': comprehensive_data.get('options', {}),
            'holders': comprehensive_data.get('holders', {}),
            'profile': comprehensive_data.get('profile', {}),
            'historical_data': comprehensive_data.get('historical_data', []),
            'financials': comprehensive_data.get('financials', {}),
            'analysis': comprehensive_data.get('analysis', {}),
            'sustainability': comprehensive_data.get('sustainability', {}),
            'insights': comprehensive_data.get('insights', {}),
            'earnings': comprehensive_data.get('earnings', {}),
            'dividends': comprehensive_data.get('dividends', {}),
            'insider_transactions': comprehensive_data.get('insider_transactions', []),
            'community': comprehensive_data.get('community', {}),
            'research': comprehensive_data.get('research', {}),
            'valuation': comprehensive_data.get('valuation', {}),  # Intrinsic/extrinsic value
            # Include raw comprehensive data for future use (contains ALL sections)
            'yahoo_comprehensive': comprehensive_data,
        }
        
        # Normalize news items - ensure links are always included
        normalized_news = []
        for item in news_items:
            # Handle nested structure where data is inside 'summary' object
            # (Yahoo Finance API sometimes returns this structure)
            if item.get("summary") and isinstance(item.get("summary"), dict):
                summary = item.get("summary", {})
                title = summary.get("title") or item.get("title")
                # Try multiple URL sources from nested structure
                link = (
                    summary.get("canonicalUrl", {}).get("url") or
                    summary.get("clickThroughUrl", {}).get("url") or
                    summary.get("previewUrl") or
                    item.get("link") or
                    item.get("url") or
                    item.get("article_url", "")
                )
                publisher = (
                    summary.get("provider", {}).get("displayName") or
                    summary.get("provider", {}).get("name") or
                    item.get("publisher") or
                    item.get("source", "Yahoo Finance")
                )
                summary_text = summary.get("summary") or summary.get("description") or item.get("description") or item.get("summary", "")
                published = (
                    summary.get("pubDate") or
                    summary.get("displayTime") or
                    item.get("publishedAt") or
                    item.get("published", "")
                )
            else:
                # Handle flat structure (original format)
                title = item.get("title")
                link = item.get("link") or item.get("url") or item.get("article_url", "")
                publisher = item.get("publisher") or item.get("source", "Yahoo Finance")
                summary_text = item.get("description") or item.get("summary", "")
                published = item.get("publishedAt") or item.get("published", "")
            
            # Ensure link is a full URL
            if link and not link.startswith("http"):
                if link.startswith("/"):
                    link = f"https://finance.yahoo.com{link}"
                else:
                    link = f"https://finance.yahoo.com/{link}"
            
            if title and link:  # Only include items with both title and link
                normalized_news.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "url": link,  # Include both for compatibility
                    "summary": summary_text,
                    "published": published,
                })
        
        # Update or create snapshot with comprehensive data
        # NOTE: StockWatchSnapshot stores PUBLIC stock data accessible to ALL users.
        # This data is shared across the entire application - any user can access it.
        snapshot, created = StockWatchSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                "payload": payload,
                "news_items": normalized_news,
                "current_price": current_price,
                "change_percent": change_percent,
                "fetched_at": timezone.now(),
                "last_error": "",
            },
        )
        
        # Update watchlist entries if they exist
        StockWatchlistEntry.objects.filter(symbol=symbol).update(
            snapshot=snapshot,
            last_refreshed=timezone.now(),
        )
        
        logger.info(
            f"Successfully scraped comprehensive Yahoo Finance data for {symbol}. "
            f"Summary fields: {len(summary)}, News items: {len(normalized_news)}, "
            f"Statistics: {len(comprehensive_data.get('statistics', {}))}"
        )
        
        return {
            "success": True,
            "symbol": symbol,
            "created": created,
            "current_price": float(current_price) if current_price else None,
            "change_percent": float(change_percent) if change_percent else None,
            "summary_fields": len(summary),
            "news_count": len(normalized_news),
            "statistics_count": len(comprehensive_data.get('statistics', {})),
            "has_options": bool(comprehensive_data.get('options', {}).get('calls') or comprehensive_data.get('options', {}).get('puts')),
            "has_holders": bool(comprehensive_data.get('holders', {}).get('institutional_holders') or comprehensive_data.get('holders', {}).get('mutual_fund_holders')),
            "has_profile": bool(comprehensive_data.get('profile', {})),
            "fetched_at": snapshot.fetched_at.isoformat() if snapshot.fetched_at else None,
        }
        
    except Exception as exc:
        error_msg = f"Failed to scrape Yahoo Finance for {symbol}: {str(exc)}"
        logger.exception(error_msg)
        
        # Update snapshot with error
        StockWatchSnapshot.objects.update_or_create(
            symbol=symbol,
            defaults={
                "last_error": error_msg,
                "fetched_at": timezone.now(),
            },
        )
        
        return {
            "success": False,
            "symbol": symbol,
            "error": error_msg,
        }


@shared_task
def populate_stock_details_background(symbol: str) -> Dict:
    """
    Background task to populate stock details for a symbol.
    This ensures stock details are available before price retrieval.
    
    This task:
    1. Scrapes comprehensive Yahoo Finance data
    2. Stores it in StockWatchSnapshot
    3. Makes it available for immediate use
    
    Args:
        symbol: Stock symbol to populate
    
    Returns:
        Dictionary with success status
    """
    symbol = symbol.upper().strip()
    logger.info(f"Populating stock details for {symbol} in background")
    
    # Call comprehensive scraper directly (already a Celery task, so it will run async)
    # This allows the task to complete without blocking
    return scrape_yahoo_finance_comprehensive(symbol)


@shared_task
def refresh_all_stock_snapshots_comprehensive() -> Dict:
    """
    Refresh all stock snapshots with comprehensive Yahoo Finance data.
    This runs for all symbols in watchlist entries.
    
    Returns:
        Dictionary with summary of refresh operation
    """
    symbols = list(
        StockWatchlistEntry.objects.values_list("symbol", flat=True).distinct()
    )
    
    logger.info(f"Refreshing comprehensive data for {len(symbols)} symbols")
    
    results = {
        "total": len(symbols),
        "successful": 0,
        "failed": 0,
        "symbols": {},
    }
    
    for symbol in symbols:
        try:
            result = scrape_yahoo_finance_comprehensive(symbol)
            if result.get("success"):
                results["successful"] += 1
            else:
                results["failed"] += 1
            results["symbols"][symbol] = result
        except Exception as exc:
            logger.exception(f"Error refreshing {symbol}")
            results["failed"] += 1
            results["symbols"][symbol] = {
                "success": False,
                "error": str(exc),
            }
    
    logger.info(
        f"Completed comprehensive refresh: {results['successful']} successful, "
        f"{results['failed']} failed out of {results['total']} total"
    )
    
    return results


@shared_task
def periodic_refresh_stock_data():
    """
    Periodic task to refresh stock data for all watchlist symbols.
    This should be scheduled to run every hour or as needed.
    
    Usage in settings.py:
        from celery.schedules import crontab
        CELERY_BEAT_SCHEDULE = {
            'refresh-stock-data': {
                'task': 'apps.stock_analysis.tasks.periodic_refresh_stock_data',
                'schedule': crontab(minute=0),  # Every hour
            },
        }
    """
    logger.info("Starting periodic refresh of stock data")
    
    # Get all unique symbols from watchlist entries
    symbols = list(
        StockWatchlistEntry.objects.values_list("symbol", flat=True).distinct()
    )
    
    if not symbols:
        logger.info("No symbols in watchlist to refresh")
        return {
            "success": True,
            "message": "No symbols to refresh",
            "total": 0,
        }
    
    logger.info(f"Refreshing {len(symbols)} symbols periodically")
    
    # Refresh each symbol asynchronously
    results = {
        "total": len(symbols),
        "triggered": 0,
        "errors": 0,
    }
    
    for symbol in symbols:
        try:
            # Trigger async refresh for each symbol
            scrape_yahoo_finance_comprehensive.delay(symbol)
            results["triggered"] += 1
        except Exception as exc:
            logger.error(f"Error triggering refresh for {symbol}: {exc}")
            results["errors"] += 1
    
    logger.info(
        f"Periodic refresh triggered: {results['triggered']} symbols, "
        f"{results['errors']} errors out of {results['total']} total"
    )
    
    return results
