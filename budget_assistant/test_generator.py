#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: test_generator.py
Description: Generate realistic synthetic transaction sets for testing
             summary statistics and alert rules. Supports edge cases
             such as zero spending and all-uncategorized transactions.
Author: Group C09
"""

import random
from datetime import date, timedelta
from typing import List, Optional

from models import Transaction, BudgetRule


def generate_transactions(
    count: int = 50,
    start_date: date = None,
    end_date: date = None,
    categories: List[str] = None,
    seed: Optional[int] = None,
) -> List[Transaction]:
    """
    Create a realistic-looking list of random transactions.

    Args:
        count: Number of transactions to generate.
        start_date: Earliest transaction date (defaults to 30 days ago).
        end_date: Latest transaction date (defaults to today).
        categories: Pool of category names to draw from.
        seed: Optional random seed for reproducible test data.

    Returns:
        List of Transaction objects with realistic amounts and descriptions.
    """
    if seed is not None:
        random.seed(seed)

    if start_date is None:
        start_date = date.today() - timedelta(days=30)
    if end_date is None:
        end_date = date.today()
    if categories is None:
        categories = ["Food", "Transport", "Entertainment", "Shopping", "Utilities",
                      "Subscriptions", "Health", "Education", "Others"]

    # Realistic descriptions mapped by category
    descriptions = {
        "Food": ["Lunch at canteen", "Coffee", "Dinner with friends", "Snacks",
                 "Breakfast", "Bubble tea", "Supermarket groceries", "Fruit"],
        "Transport": ["MTR fare", "Bus ride", "Taxi", "Uber", "Octopus top-up",
                      "Ferry ticket", "Minibus"],
        "Entertainment": ["Movie ticket", "Netflix", "Spotify", "Arcade",
                          "Karaoke", "Concert ticket", "Game purchase"],
        "Shopping": ["Clothing", "Shoes", "Stationery", "Phone accessory",
                     "Online order", "Gift", "Cosmetics"],
        "Utilities": ["Mobile bill", "Electricity", "Water bill", "Internet",
                      "Laundry"],
        "Subscriptions": ["Gym membership", "Cloud storage", "VPN", "Magazine",
                          "Software license"],
        "Health": ["Pharmacy", "Clinic visit", "Dental check", "Vitamins",
                   "First aid"],
        "Education": ["Textbook", "Course fee", "Printing", "Tutorial",
                      "Exam materials"],
        "Others": ["Unknown", "Misc", "Cash withdrawal", "Refund", "Fine"],
    }

    transactions: List[Transaction] = []
    span_days = (end_date - start_date).days

    for txn_id in range(1, count + 1):
        # Random date within the window
        offset = random.randint(0, max(span_days, 0))
        txn_date = start_date + timedelta(days=offset)

        cat = random.choice(categories)
        desc_pool = descriptions.get(cat, ["Purchase"])
        desc = random.choice(desc_pool)

        # Amounts vary by category for realism
        if cat == "Food":
            amount = round(random.uniform(10, 150), 2)
        elif cat == "Transport":
            amount = round(random.uniform(5, 80), 2)
        elif cat == "Entertainment":
            amount = round(random.uniform(30, 300), 2)
        elif cat == "Shopping":
            amount = round(random.uniform(50, 500), 2)
        elif cat == "Utilities":
            amount = round(random.uniform(50, 400), 2)
        elif cat == "Subscriptions":
            amount = round(random.uniform(10, 200), 2)
        elif cat == "Health":
            amount = round(random.uniform(20, 250), 2)
        elif cat == "Education":
            amount = round(random.uniform(30, 400), 2)
        else:
            amount = round(random.uniform(1, 100), 2)

        transactions.append(
            Transaction(
                txn_id=txn_id,
                date=txn_date,
                amount=amount,
                category=cat,
                description=desc,
            )
        )

    # Sort by date for nicer display
    transactions.sort(key=lambda t: (t.date, t.txn_id))
    return transactions


def generate_zero_spending_case() -> List[Transaction]:
    """
    Edge case: a period with absolutely no transactions.
    Useful for testing alert silence and zero-division guards.
    """
    return []


def generate_all_uncategorized(count: int = 10) -> List[Transaction]:
    """
    Edge case: every transaction is placed in the generic 'Others' bucket.
    Useful for testing uncategorized warnings.
    """
    transactions = []
    today = date.today()
    for i in range(1, count + 1):
        transactions.append(
            Transaction(
                txn_id=i,
                date=today - timedelta(days=i),
                amount=round(random.uniform(10, 100), 2),
                category="Others",
                description="Unclassified purchase",
            )
        )
    return transactions


def generate_sample_rules() -> List[BudgetRule]:
    """
    Produce a sensible default set of budget rules for demonstration.
    """
    return [
        BudgetRule(rule_id=1, category="Food", period="daily", threshold=50.0, alert_type="cap"),
        BudgetRule(rule_id=2, category="Transport", period="monthly", threshold=500.0, alert_type="cap"),
        BudgetRule(rule_id=3, category="*", period="monthly", threshold=2000.0, alert_type="cap"),
        BudgetRule(rule_id=4, category="Entertainment", period="monthly", threshold=20.0, alert_type="percentage"),
        BudgetRule(rule_id=5, category="Food", period="daily", threshold=50.0, alert_type="cap"),
    ]
