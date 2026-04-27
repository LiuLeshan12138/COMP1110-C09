#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: statistics.py
Description: Compute summary statistics from transaction data, including
             totals by category, time-based breakdowns, trend analysis,
             and top-category identification.
Author: Group C09
"""

from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Tuple, Optional

from models import Transaction


def total_spending(transactions: List[Transaction]) -> float:
    """Return the grand total of all transaction amounts."""
    return sum(t.amount for t in transactions)


def total_by_category(transactions: List[Transaction]) -> Dict[str, float]:
    """
    Aggregate spending grouped by category.

    Returns:
        Dictionary mapping category name -> total amount spent.
    """
    result: Dict[str, float] = defaultdict(float)
    for t in transactions:
        result[t.category] += t.amount
    return dict(result)


def total_by_period(
    transactions: List[Transaction],
    period: str = "daily",
) -> Dict[str, float]:
    """
    Aggregate spending by a chosen time period.

    Args:
        transactions: List of Transaction objects.
        period: One of "daily", "weekly", "monthly", "yearly".

    Returns:
        Dictionary mapping period key -> total amount.
        Keys are formatted as YYYY-MM-DD, YYYY-WNN, YYYY-MM, or YYYY.
    """
    result: Dict[str, float] = defaultdict(float)
    for t in transactions:
        if period == "daily":
            key = t.date.isoformat()
        elif period == "weekly":
            # ISO calendar week: YYYY-WNN
            key = f"{t.date.year}-W{t.date.isocalendar()[1]:02d}"
        elif period == "monthly":
            key = t.date.strftime("%Y-%m")
        elif period == "yearly":
            key = str(t.date.year)
        else:
            raise ValueError("period must be daily, weekly, monthly, or yearly")
        result[key] += t.amount
    return dict(result)


def top_categories(
    transactions: List[Transaction],
    n: int = 3,
) -> List[Tuple[str, float]]:
    """
    Return the top N categories by total spending, sorted descending.

    Args:
        transactions: List of Transaction objects.
        n: Maximum number of categories to return.

    Returns:
        List of (category, total_amount) tuples.
    """
    by_cat = total_by_category(transactions)
    sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)
    return sorted_cats[:n]


def spending_trend(
    transactions: List[Transaction],
    days: int = 7,
    end_date: Optional[date] = None,
) -> Dict[str, float]:
    """
    Compute daily spending for the last `days` days ending at `end_date`.

    Args:
        transactions: List of Transaction objects.
        days: Number of days to look back.
        end_date: The last day of the trend window (defaults to today).

    Returns:
        Dictionary mapping each date string (YYYY-MM-DD) -> amount.
        Dates with no transactions are included with 0.0.
    """
    if end_date is None:
        end_date = date.today()

    # Initialise every day in the window with 0.0
    result: Dict[str, float] = {}
    for offset in range(days):
        d = end_date - timedelta(days=offset)
        result[d.isoformat()] = 0.0

    for t in transactions:
        if t.date in [end_date - timedelta(days=o) for o in range(days)]:
            result[t.date.isoformat()] += t.amount

    # Return chronologically oldest -> newest
    return dict(sorted(result.items()))


def average_daily_spending(transactions: List[Transaction]) -> float:
    """
    Calculate average spending per day across the recorded date range.
    If all transactions are on the same day, returns that day's total.
    """
    if not transactions:
        return 0.0
    dates = [t.date for t in transactions]
    min_date = min(dates)
    max_date = max(dates)
    span_days = (max_date - min_date).days + 1
    return total_spending(transactions) / span_days


def percentage_of_total(transactions: List[Transaction], category: str) -> float:
    """
    Compute what percentage of total spending belongs to a given category.

    Returns:
        Float percentage in the range [0.0, 100.0]. Returns 0.0 if
        there are no transactions at all.
    """
    total = total_spending(transactions)
    if total == 0:
        return 0.0
    cat_total = sum(t.amount for t in transactions if t.category == category)
    return (cat_total / total) * 100.0


def filter_transactions(
    transactions: List[Transaction],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> List[Transaction]:
    """
    Filter transactions by multiple optional criteria.

    Args:
        transactions: Source list of Transaction objects.
        start_date: Only include transactions on or after this date.
        end_date: Only include transactions on or before this date.
        category: Only include transactions matching this category.
        min_amount: Only include transactions with amount >= this value.
        max_amount: Only include transactions with amount <= this value.

    Returns:
        A new list containing only matching transactions.
    """
    result = []
    for t in transactions:
        if start_date is not None and t.date < start_date:
            continue
        if end_date is not None and t.date > end_date:
            continue
        if category is not None and t.category != category:
            continue
        if min_amount is not None and t.amount < min_amount:
            continue
        if max_amount is not None and t.amount > max_amount:
            continue
        result.append(t)
    return result
