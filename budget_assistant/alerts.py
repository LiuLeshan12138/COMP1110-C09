#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: alerts.py
Description: Rule-based alert engine. Evaluates BudgetRule objects against
             the current transaction list and produces human-readable alert
             messages when thresholds are breached.
Author: Group C09
"""

from datetime import date, timedelta
from typing import List, Dict, Tuple

from models import Transaction, BudgetRule
from statistics import total_spending, total_by_category, total_by_period, percentage_of_total


def _period_window(period: str, reference_date: date) -> Tuple[date, date]:
    """
    Compute the start and end dates for a budget period relative to
    the reference date.

    Args:
        period: One of "daily", "weekly", "monthly", "yearly".
        reference_date: The anchor date (usually today).

    Returns:
        Tuple (start_date, end_date) inclusive.
    """
    if period == "daily":
        return reference_date, reference_date
    elif period == "weekly":
        # ISO week starts on Monday
        monday = reference_date - timedelta(days=reference_date.weekday())
        return monday, monday + timedelta(days=6)
    elif period == "monthly":
        start = reference_date.replace(day=1)
        # Find last day of month by going to first of next month then back one day
        if reference_date.month == 12:
            next_month = reference_date.replace(year=reference_date.year + 1, month=1, day=1)
        else:
            next_month = reference_date.replace(month=reference_date.month + 1, day=1)
        end = next_month - timedelta(days=1)
        return start, end
    elif period == "yearly":
        start = reference_date.replace(month=1, day=1)
        end = reference_date.replace(month=12, day=31)
        return start, end
    else:
        raise ValueError(f"Unsupported period: {period}")


def evaluate_rules(
    transactions: List[Transaction],
    rules: List[BudgetRule],
    reference_date: date = None,
) -> List[str]:
    """
    Evaluate all budget rules against the transaction history.

    For each rule, the system calculates the relevant spending in the rule's
    time window and generates an alert if the threshold is exceeded.

    Args:
        transactions: Full transaction history.
        rules: Active budget rules.
        reference_date: Date to evaluate from (defaults to today).

    Returns:
        A list of alert message strings. Empty if no rules are breached.
    """
    if reference_date is None:
        reference_date = date.today()

    alerts: List[str] = []

    for rule in rules:
        start, end = _period_window(rule.period, reference_date)
        # Filter transactions to the rule's window
        relevant = [t for t in transactions if start <= t.date <= end]

        if rule.category == "*":
            spent = total_spending(relevant)
        else:
            spent = sum(t.amount for t in relevant if t.category == rule.category)

        if rule.alert_type == "cap":
            if spent > rule.threshold:
                alerts.append(
                    f"ALERT [Rule {rule.rule_id}] "
                    f"{rule.category} spending (${spent:,.2f}) "
                    f"exceeds {rule.period} cap (${rule.threshold:,.2f}) "
                    f"for period {start.isoformat()} ~ {end.isoformat()}."
                )
        elif rule.alert_type == "percentage":
            total = total_spending(relevant)
            if total > 0:
                pct = (spent / total) * 100.0
                if pct > rule.threshold:
                    alerts.append(
                        f"ALERT [Rule {rule.rule_id}] "
                        f"{rule.category} takes {pct:.1f}% of total, "
                        f"exceeds {rule.period} threshold ({rule.threshold:.1f}%)."
                    )
    return alerts


def detect_consecutive_overspend(
    transactions: List[Transaction],
    category: str,
    threshold: float,
    min_days: int = 3,
) -> List[str]:
    """
    Detect consecutive days where a category's daily spending exceeds
    a given threshold.

    Args:
        transactions: Full transaction history.
        category: Category to monitor.
        threshold: Daily spending cap.
        min_days: Minimum number of consecutive overspend days to trigger.

    Returns:
        Alert messages for each detected streak.
    """
    alerts: List[str] = []
    daily = total_by_period(transactions, period="daily")
    # Filter to the target category only — recompute per-day manually
    cat_daily: Dict[str, float] = {}
    for t in transactions:
        if t.category == category:
            d = t.date.isoformat()
            cat_daily[d] = cat_daily.get(d, 0.0) + t.amount

    if not cat_daily:
        return []

    sorted_days = sorted(cat_daily.keys())
    streak = 0
    streak_start = None

    for d in sorted_days:
        if cat_daily[d] > threshold:
            if streak == 0:
                streak_start = d
            streak += 1
        else:
            if streak >= min_days:
                alerts.append(
                    f"ALERT Consecutive overspend on {category}: "
                    f"{streak} days from {streak_start} to {d}. "
                    f"Daily cap: ${threshold:,.2f}."
                )
            streak = 0
            streak_start = None

    # Handle streak that runs to the end of data
    if streak >= min_days:
        alerts.append(
            f"ALERT Consecutive overspend on {category}: "
            f"{streak} days from {streak_start} to {sorted_days[-1]}. "
            f"Daily cap: ${threshold:,.2f}."
        )

    return alerts


def detect_uncategorized(transactions: List[Transaction]) -> List[str]:
    """
    Warn about transactions that fall into a generic or empty category.
    In this system 'Others' is considered the catch-all uncategorized bucket.

    Args:
        transactions: Full transaction history.

    Returns:
        Alert messages if any uncategorized transactions exist.
    """
    uncategorized = [t for t in transactions if t.category in {"Others", "Uncategorized", ""}]
    if uncategorized:
        return [
            f"ALERT {len(uncategorized)} transaction(s) are uncategorized or marked 'Others'. "
            f"Please review and assign proper categories."
        ]
    return []
