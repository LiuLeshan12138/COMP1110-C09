#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: models.py
Description: Core data models for transactions, budget rules, and categories.
             This module defines the schema for all data structures used
             throughout the application.
Author: Group C09
"""

from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Transaction:
    """
    Represents a single spending transaction.

    Attributes:
        txn_id: Unique identifier for the transaction (auto-generated).
        date: The date when the spending occurred (YYYY-MM-DD).
        amount: The monetary value spent (non-negative float).
        category: Spending category (e.g., 'Food', 'Transport').
        description: Short human-readable note about the transaction.
        notes: Optional extra details.
    """
    txn_id: int
    date: date
    amount: float
    category: str
    description: str
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate transaction fields after initialization."""
        if self.amount < 0:
            raise ValueError("Transaction amount cannot be negative.")
        # Normalize category to title case for consistent grouping
        self.category = self.category.strip().title()

    def to_dict(self) -> dict:
        """Serialize the transaction to a plain dictionary for JSON export."""
        return {
            "txn_id": self.txn_id,
            "date": self.date.isoformat(),
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        """Reconstruct a Transaction instance from a dictionary."""
        return cls(
            txn_id=int(data["txn_id"]),
            date=date.fromisoformat(data["date"]),
            amount=float(data["amount"]),
            category=data["category"],
            description=data["description"],
            notes=data.get("notes"),
        )

    def __str__(self) -> str:
        """Human-readable single-line representation."""
        return (
            f"[{self.txn_id}] {self.date.isoformat()} | "
            f"${self.amount:,.2f} | {self.category} | {self.description}"
        )


@dataclass
class BudgetRule:
    """
    Represents a budget constraint that triggers alerts when exceeded.

    Attributes:
        rule_id: Unique identifier for the rule.
        category: Target spending category ("*" means all categories).
        period: Time window — "daily", "weekly", "monthly", or "yearly".
        threshold: Maximum allowed spending amount in the period.
        alert_type: Either "cap" (hard limit) or "percentage" (ratio alert).
    """
    rule_id: int
    category: str
    period: str
    threshold: float
    alert_type: str  # "cap" or "percentage"

    def __post_init__(self):
        """Validate budget rule fields after initialization."""
        valid_periods = {"daily", "weekly", "monthly", "yearly"}
        if self.period not in valid_periods:
            raise ValueError(f"Period must be one of {valid_periods}.")
        if self.threshold < 0:
            raise ValueError("Threshold cannot be negative.")
        if self.alert_type not in {"cap", "percentage"}:
            raise ValueError("alert_type must be 'cap' or 'percentage'.")
        self.category = self.category.strip().title() if self.category != "*" else "*"

    def to_dict(self) -> dict:
        """Serialize the rule to a plain dictionary."""
        return {
            "rule_id": self.rule_id,
            "category": self.category,
            "period": self.period,
            "threshold": self.threshold,
            "alert_type": self.alert_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BudgetRule":
        """Reconstruct a BudgetRule instance from a dictionary."""
        return cls(
            rule_id=int(data["rule_id"]),
            category=data["category"],
            period=data["period"],
            threshold=float(data["threshold"]),
            alert_type=data["alert_type"],
        )

    def __str__(self) -> str:
        """Human-readable single-line representation."""
        cat = "All" if self.category == "*" else self.category
        return (
            f"[Rule {self.rule_id}] {cat} — {self.period} "
            f"{self.alert_type} @ ${self.threshold:,.2f}"
        )


# ---------------------------------------------------------------------------
# Default category list used when the user has not configured custom ones.
# ---------------------------------------------------------------------------
DEFAULT_CATEGORIES: List[str] = [
    "Food",
    "Transport",
    "Entertainment",
    "Shopping",
    "Utilities",
    "Subscriptions",
    "Health",
    "Education",
    "Others",
]
