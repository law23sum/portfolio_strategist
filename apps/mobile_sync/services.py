"""Services that assemble serialized payloads for the mobile client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.chat.models import Chat, ChatMessage
from apps.records.financial_aggregation import (
    BudgetAggregationService,
    DashboardAggregationService,
    DebtAggregationService,
    InvestmentAggregationService,
)
from apps.records.models import LinkedAccount
from apps.records.services import get_document_metrics
from apps.stock_analysis.models import StockAnalysis, StockWatchlistEntry

User = get_user_model()


def _decimal_to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return value


def _date_to_str(value):
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _datetime_to_str(value):
    if value is None:
        return None
    if hasattr(value, "tzinfo") and value.tzinfo is None:
        value = timezone.make_aware(value, timezone.utc)
    if hasattr(value, "tzinfo"):
        value = timezone.localtime(value)
    return value.isoformat()


def normalize_scope(sections: Iterable[str] | None) -> str:
    """Create a stable scope key for the selected sections."""
    allowed = MobileDataAssembler.ALL_SECTIONS
    if not sections:
        return "all"
    filtered = sorted({section for section in sections if section in allowed})
    return "+".join(filtered) if filtered else "all"


@dataclass
class MobileDataAssembler:
    """Collects all data needed by the mobile client."""

    user: User
    recent_limit: int = 10
    stock_limit: int = 3
    document_limit: int = 15
    chat_limit: int = 3

    ALL_SECTIONS: Sequence[str] = (
        "user",
        "dashboard",
        "budget",
        "investments",
        "debt",
        "records",
        "stock",
        "chat",
    )

    def build_payload(self, sections: Iterable[str] | None = None) -> Dict:
        selected = self._normalize_sections(sections)
        builders = {
            "user": self._build_user,
            "dashboard": self._build_dashboard,
            "budget": self._build_budget,
            "investments": self._build_investments,
            "debt": self._build_debt,
            "records": self._build_records,
            "stock": self._build_stock,
            "chat": self._build_chat,
        }
        payload = {}
        for section in selected:
            builder = builders.get(section)
            if builder:
                payload[section] = builder()
        payload["metadata"] = {
            "sections": list(selected),
            "generated_at": timezone.now().isoformat(),
            "user_id": self.user.id,
            "scope": normalize_scope(selected),
        }
        return payload

    # ------------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------------
    def _build_user(self) -> Dict:
        user = self.user
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": _datetime_to_str(user.date_joined),
            "last_login": _datetime_to_str(user.last_login),
        }

    def _build_dashboard(self) -> Dict:
        summary = DashboardAggregationService.get_user_financial_summary(self.user)
        transactions = summary.pop("recent_transactions", [])
        summary["recent_transactions"] = self._serialize_transactions(transactions)
        return summary

    def _build_budget(self) -> Dict:
        data = BudgetAggregationService.get_user_budget_data(self.user, days=30)
        balances = []
        for entry in data.get("account_balances", []):
            account = entry.get("account")
            balance = entry.get("balance")
            balances.append(
                {
                    "account_id": getattr(account, "id", None),
                    "account_name": getattr(account, "account_name", ""),
                    "account_type": getattr(account, "account_type", ""),
                    "institution_name": getattr(account, "institution_name", ""),
                    "current_balance": _decimal_to_float(getattr(balance, "current_balance", None)),
                    "available_balance": _decimal_to_float(getattr(balance, "available_balance", None)),
                    "limit": _decimal_to_float(getattr(balance, "limit", None)),
                    "balance_date": _date_to_str(getattr(balance, "balance_date", None)),
                }
            )
        data["account_balances"] = balances
        data["recent_transactions"] = self._serialize_transactions(data.get("recent_transactions", []))
        return data

    def _build_investments(self) -> Dict:
        data = InvestmentAggregationService.get_user_investment_data(self.user)
        summaries = []
        for entry in data.get("account_summaries", []):
            account = entry.get("account")
            summaries.append(
                {
                    "account_id": getattr(account, "id", None),
                    "account_name": getattr(account, "account_name", ""),
                    "institution_name": getattr(account, "institution_name", ""),
                    "account_type": getattr(account, "account_type", ""),
                    "value": entry.get("value"),
                    "holdings_count": entry.get("holdings_count"),
                }
            )
        data["account_summaries"] = summaries
        data["recent_transactions"] = self._serialize_investment_transactions(data.get("recent_transactions", []))
        return data

    def _build_debt(self) -> Dict:
        data = DebtAggregationService.get_user_debt_data(self.user)
        details = []
        for entry in data.get("account_details", []):
            account = entry.get("account")
            balance = entry.get("balance")
            details.append(
                {
                    "account_id": getattr(account, "id", None),
                    "account_name": getattr(account, "account_name", ""),
                    "account_type": getattr(account, "account_type", ""),
                    "current_balance": _decimal_to_float(getattr(balance, "current_balance", None)),
                    "interest_rate": _decimal_to_float(getattr(balance, "interest_rate", None)),
                    "limit": _decimal_to_float(getattr(balance, "limit", None)),
                    "debt_type": entry.get("debt_type"),
                    "balance_date": _date_to_str(getattr(balance, "balance_date", None)),
                }
            )
        data["account_details"] = details
        return data

    def _build_records(self) -> Dict:
        metrics = get_document_metrics()
        recent_docs = []
        for doc in metrics.get("recent_documents", [])[: self.document_limit]:
            recent_docs.append(
                {
                    "id": doc.id,
                    "name": doc.name,
                    "record_type": doc.record_type,
                    "sub_record_type": doc.sub_record_type,
                    "year": doc.year,
                    "processed": doc.processed,
                    "uploaded_at": _datetime_to_str(doc.uploaded_at),
                }
            )
        metrics["recent_documents"] = recent_docs
        metrics["linked_accounts"] = self._serialize_linked_accounts()
        return metrics

    def _build_stock(self) -> Dict:
        analyses = StockAnalysis.objects.filter(user=self.user).order_by("-analysis_date")[: self.stock_limit]
        analysis_payload = []
        for analysis in analyses:
            analysis_payload.append(
                {
                    "id": analysis.id,
                    "symbol": analysis.symbol,
                    "analysis_date": _datetime_to_str(analysis.analysis_date),
                    "stock_data": analysis.stock_data,
                    "ratios_table": analysis.ratios_table,
                    "ai_assessment": analysis.ai_assessment,
                    "forecast_data": analysis.forecast_data,
                    "news_html": analysis.news_html,
                    "equation_type": analysis.equation_type,
                    "forecast_days": analysis.forecast_days,
                }
            )
        watchlist_entries = (
            StockWatchlistEntry.objects.filter(user=self.user)
            .select_related("snapshot")
            .order_by("symbol")[: self.stock_limit * 3]
        )
        watchlist = []
        for entry in watchlist_entries:
            snapshot = entry.snapshot
            watchlist.append(
                {
                    "id": entry.id,
                    "symbol": entry.symbol,
                    "nickname": entry.nickname,
                    "last_refreshed": _datetime_to_str(entry.last_refreshed),
                    "current_price": _decimal_to_float(getattr(snapshot, "current_price", None)),
                    "change_percent": _decimal_to_float(getattr(snapshot, "change_percent", None)),
                    "payload": getattr(snapshot, "payload", {}),
                }
            )
        return {
            "analyses": analysis_payload,
            "watchlist": watchlist,
        }

    def _build_chat(self) -> Dict:
        chats = Chat.objects.filter(user=self.user).order_by("-updated_at")[: self.chat_limit]
        chat_payload = []
        for chat in chats:
            last_message = chat.messages.order_by("-created_at").first()
            chat_payload.append(
                {
                    "id": chat.id,
                    "name": chat.name,
                    "created_at": _datetime_to_str(chat.created_at),
                    "updated_at": _datetime_to_str(chat.updated_at),
                    "messages_count": chat.messages.count(),
                    "last_message": self._serialize_chat_message(last_message),
                }
            )
        return {"recent_chats": chat_payload}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_sections(self, sections: Iterable[str] | None) -> List[str]:
        if not sections:
            return list(self.ALL_SECTIONS)
        selected = [section for section in sections if section in self.ALL_SECTIONS]
        return selected or list(self.ALL_SECTIONS)

    def _serialize_transactions(self, transactions: Sequence) -> List[Dict]:
        serialized = []
        for tx in transactions[: self.recent_limit]:
            serialized.append(
                {
                    "id": getattr(tx, "id", None),
                    "date": _date_to_str(getattr(tx, "date", None)),
                    "amount": _decimal_to_float(getattr(tx, "amount", None)),
                    "description": getattr(tx, "description", ""),
                    "category": getattr(tx, "category", ""),
                    "account_name": getattr(getattr(tx, "account", None), "account_name", ""),
                    "transaction_type": getattr(tx, "transaction_type", ""),
                }
            )
        return serialized

    def _serialize_investment_transactions(self, transactions: Sequence) -> List[Dict]:
        serialized = []
        for tx in transactions[: self.recent_limit]:
            serialized.append(
                {
                    "id": getattr(tx, "id", None),
                    "date": _date_to_str(getattr(tx, "date", None)),
                    "transaction_type": getattr(tx, "transaction_type", ""),
                    "amount": _decimal_to_float(getattr(tx, "amount", None)),
                    "security_name": getattr(tx, "security_name", ""),
                    "security_ticker": getattr(tx, "security_ticker", ""),
                    "account_name": getattr(getattr(tx, "account", None), "account_name", ""),
                }
            )
        return serialized

    def _serialize_chat_message(self, message: ChatMessage | None) -> Dict | None:
        if not message:
            return None
        return {
            "id": message.id,
            "type": message.message_type,
            "content": message.content,
            "created_at": _datetime_to_str(message.created_at),
        }

    def _serialize_linked_accounts(self) -> List[Dict]:
        accounts = LinkedAccount.objects.filter(user=self.user).select_related("provider").order_by("institution_name")
        serialized = []
        for account in accounts:
            latest_balance = account.balances.first()
            serialized.append(
                {
                    "id": account.id,
                    "institution_name": account.institution_name,
                    "account_name": account.account_name,
                    "account_type": account.account_type,
                    "account_subtype": account.account_subtype,
                    "status": account.status,
                    "current_balance": _decimal_to_float(getattr(latest_balance, "current_balance", None)),
                    "available_balance": _decimal_to_float(getattr(latest_balance, "available_balance", None)),
                    "balance_date": _date_to_str(getattr(latest_balance, "balance_date", None)),
                }
            )
        return serialized
