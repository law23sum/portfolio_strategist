"""Helper utilities for financial record insights and navigation."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from django.db.models import Count, Q, Sum

from .models import (
    ExtractedField,
    FinancialDocument,
    LinkedAccount,
    AccountBalance,
    FinancialTransaction,
    InvestmentHolding,
    DebtAccount,
)

RecordTree = List[Dict[str, object]]


def _record_type_labels() -> Dict[str, str]:
    return dict(FinancialDocument.RECORD_TYPE_CHOICES)


def _subcategory_labels() -> Dict[str, Dict[str, str]]:
    return {key: dict(options) for key, options in FinancialDocument.SUBCATEGORY_OPTIONS.items()}


def get_document_metrics() -> Dict[str, object]:
    """Aggregate counts and helper data for dashboards."""

    # Use fresh querysets for each operation to avoid aggregate conflicts
    totals_raw = FinancialDocument.objects.aggregate(
        total=Count("id"),
        processed_count=Count("id", filter=Q(processed=True)),
        pending_count=Count("id", filter=Q(processed=False)),
    )
    totals = {
        "total": totals_raw.get("total", 0) or 0,
        "processed": totals_raw.get("processed_count", 0) or 0,
        "pending": totals_raw.get("pending_count", 0) or 0,
    }

    type_labels = _record_type_labels()
    subcategory_labels = _subcategory_labels()

    documents_by_type = [
        {
            "record_type": row["record_type"],
            "label": type_labels.get(row["record_type"], row["record_type"].replace("_", " ").title()),
            "count": row["count"],
        }
        for row in FinancialDocument.objects.values("record_type").annotate(count=Count("id")).order_by("-count")
    ]

    documents_by_year = list(
        FinancialDocument.objects.values("year").annotate(count=Count("id")).order_by("year")
    )

    coverage_by_type = []
    for record_type, label in FinancialDocument.RECORD_TYPE_CHOICES:
        subchoices = subcategory_labels.get(record_type, {})
        total_subs = len(subchoices)
        filled = (
            FinancialDocument.objects.filter(record_type=record_type)
            .values("sub_record_type")
            .distinct()
            .count()
        )
        coverage_by_type.append(
            {
                "record_type": record_type,
                "label": label,
                "covered": filled,
                "total": total_subs,
                "percent": round(filled / total_subs * 100, 1) if total_subs else 0,
            }
        )

    coverage_by_type.sort(key=lambda item: item["percent"], reverse=True)

    subcategory_leaders = []
    subcategory_counts = (
        FinancialDocument.objects.values("record_type", "sub_record_type")
        .annotate(count=Count("id"))
        .order_by("-count")[:12]
    )
    for row in subcategory_counts:
        subcategory_leaders.append(
            {
                "record_type": row["record_type"],
                "record_label": type_labels.get(row["record_type"], row["record_type"].title()),
                "sub_record_type": row["sub_record_type"],
                "sub_label": subcategory_labels.get(row["record_type"], {}).get(
                    row["sub_record_type"], row["sub_record_type"].replace("_", " ").title()
                ),
                "count": row["count"],
            }
        )

    extracted_field_leaders = list(
        ExtractedField.objects.values("field_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    charts_payload = {
        "hasData": totals["total"] > 0,
        "byType": {
            "labels": [row["label"] for row in documents_by_type],
            "data": [row["count"] for row in documents_by_type],
        },
        "byYear": {
            "labels": [row["year"] for row in documents_by_year],
            "data": [row["count"] for row in documents_by_year],
        },
        "processing": {
            "labels": ["Processed", "Pending"],
            "data": [totals["processed"], totals["pending"]],
        },
    }

    # Include aggregated account data
    linked_accounts_count = LinkedAccount.objects.count()
    # Get latest balance for each active account and sum them
    active_accounts = LinkedAccount.objects.filter(status='active')
    total_account_balance = sum(
        account.balances.first().current_balance 
        for account in active_accounts 
        if account.balances.first()
    )
    
    return {
        "totals": totals,
        "documents_by_type": documents_by_type,
        "documents_by_year": documents_by_year,
        "coverage_by_type": coverage_by_type,
        "subcategory_leaders": subcategory_leaders,
        "recent_documents": FinancialDocument.objects.select_related("user").order_by("-uploaded_at")[:8],
        "extracted_field_leaders": extracted_field_leaders,
        "charts_payload": charts_payload,
        "linked_accounts_count": linked_accounts_count,
        "total_account_balance": total_account_balance,
    }


def build_document_library() -> RecordTree:
    """Return a record/subcategory tree with attached documents."""

    type_labels = _record_type_labels()
    subcategory_labels = _subcategory_labels()
    grouped: Dict[str, Dict[str, List[FinancialDocument]]] = defaultdict(lambda: defaultdict(list))

    for doc in (
        FinancialDocument.objects.all()
        .select_related("user")
        .order_by("record_type", "sub_record_type", "-uploaded_at")
    ):
        grouped[doc.record_type][doc.sub_record_type].append(doc)

    record_tree: RecordTree = []
    for record_type, label in FinancialDocument.RECORD_TYPE_CHOICES:
        subentries = []
        total_docs = 0
        type_group = grouped.get(record_type, {})
        for subvalue, sublabel in subcategory_labels.get(record_type, {}).items():
            documents = type_group.get(subvalue, [])
            total_docs += len(documents)
            subentries.append(
                {
                    "value": subvalue,
                    "label": sublabel,
                    "documents": documents,
                    "count": len(documents),
                    "latest_year": documents[0].year if documents else None,
                }
            )
        covered = sum(1 for entry in subentries if entry["count"])
        record_tree.append(
            {
                "record_type": record_type,
                "label": label,
                "documents_count": total_docs,
                "covered_subcategories": covered,
                "total_subcategories": len(subentries),
                "subcategories": subentries,
            }
        )

    return record_tree
