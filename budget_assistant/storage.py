#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: storage.py
Description: Handles all file input/output operations for transactions, budget
             rules, and category configuration. Uses JSON as the persistent
             storage format. Gracefully handles missing files, empty files,
             and malformed data with clear error messages.
Author: Group C09
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from models import Transaction, BudgetRule, DEFAULT_CATEGORIES


def load_transactions(filepath: str) -> List[Transaction]:
    """
    Load a list of Transaction objects from a JSON file.

    Args:
        filepath: Path to the JSON file containing transaction records.

    Returns:
        A list of Transaction instances. Returns an empty list if the file
        does not exist, is empty, or contains malformed JSON.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[Info] Transaction file not found: {filepath}. Starting with empty list.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()
            if not raw_text:
                print(f"[Info] Transaction file is empty: {filepath}. Starting with empty list.")
                return []
            data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"[Error] Failed to parse JSON in {filepath}: {exc}")
        return []
    except OSError as exc:
        print(f"[Error] Cannot read {filepath}: {exc}")
        return []

    transactions = []
    for idx, item in enumerate(data):
        try:
            txn = Transaction.from_dict(item)
            transactions.append(txn)
        except (KeyError, ValueError, TypeError) as exc:
            print(f"[Warning] Skipping malformed transaction at index {idx} in {filepath}: {exc}")
    return transactions


def save_transactions(filepath: str, transactions: List[Transaction]) -> bool:
    """
    Save a list of Transaction objects to a JSON file.

    Args:
        filepath: Destination path for the JSON file.
        transactions: List of Transaction instances to persist.

    Returns:
        True if the operation succeeded, False otherwise.
    """
    path = Path(filepath)
    try:
        # Ensure parent directories exist
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([t.to_dict() for t in transactions], f, indent=2, ensure_ascii=False)
        return True
    except OSError as exc:
        print(f"[Error] Cannot write transactions to {filepath}: {exc}")
        return False


def load_budget_rules(filepath: str) -> List[BudgetRule]:
    """
    Load a list of BudgetRule objects from a JSON file.

    Args:
        filepath: Path to the JSON file containing budget rules.

    Returns:
        A list of BudgetRule instances. Returns an empty list if the file
        does not exist, is empty, or contains malformed JSON.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[Info] Budget rules file not found: {filepath}. No rules loaded.")
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()
            if not raw_text:
                print(f"[Info] Budget rules file is empty: {filepath}. No rules loaded.")
                return []
            data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        print(f"[Error] Failed to parse JSON in {filepath}: {exc}")
        return []
    except OSError as exc:
        print(f"[Error] Cannot read {filepath}: {exc}")
        return []

    rules = []
    for idx, item in enumerate(data):
        try:
            rule = BudgetRule.from_dict(item)
            rules.append(rule)
        except (KeyError, ValueError, TypeError) as exc:
            print(f"[Warning] Skipping malformed budget rule at index {idx} in {filepath}: {exc}")
    return rules


def save_budget_rules(filepath: str, rules: List[BudgetRule]) -> bool:
    """
    Save a list of BudgetRule objects to a JSON file.

    Args:
        filepath: Destination path for the JSON file.
        rules: List of BudgetRule instances to persist.

    Returns:
        True if the operation succeeded, False otherwise.
    """
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in rules], f, indent=2, ensure_ascii=False)
        return True
    except OSError as exc:
        print(f"[Error] Cannot write budget rules to {filepath}: {exc}")
        return False


def load_categories(filepath: str) -> List[str]:
    """
    Load custom category list from a plain text file.
    Each line is treated as one category name.

    Args:
        filepath: Path to the text file.

    Returns:
        A list of category strings. Falls back to DEFAULT_CATEGORIES if
        the file does not exist or is empty.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[Info] Category config not found: {filepath}. Using defaults.")
        return DEFAULT_CATEGORIES.copy()

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            print(f"[Info] Category config is empty: {filepath}. Using defaults.")
            return DEFAULT_CATEGORIES.copy()
        return lines
    except OSError as exc:
        print(f"[Error] Cannot read {filepath}: {exc}. Using defaults.")
        return DEFAULT_CATEGORIES.copy()


def save_categories(filepath: str, categories: List[str]) -> bool:
    """
    Save a custom category list to a plain text file (one per line).

    Args:
        filepath: Destination path for the text file.
        categories: List of category strings to persist.

    Returns:
        True if the operation succeeded, False otherwise.
    """
    path = Path(filepath)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for cat in categories:
                f.write(cat + "\n")
        return True
    except OSError as exc:
        print(f"[Error] Cannot write categories to {filepath}: {exc}")
        return False
