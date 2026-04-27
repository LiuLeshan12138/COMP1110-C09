#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: main.py
Description: Main entry point and text-based menu interface. Provides
             interactive options for adding, viewing, filtering,
             summarizing transactions, managing budget rules, and
             running alerts. All user input is validated.
Author: Group C09
"""

import sys
from datetime import date, datetime
from typing import List

from models import Transaction, BudgetRule, DEFAULT_CATEGORIES
from storage import (
    load_transactions,
    save_transactions,
    load_budget_rules,
    save_budget_rules,
    load_categories,
    save_categories,
)
from statistics import (
    total_spending,
    total_by_category,
    total_by_period,
    top_categories,
    spending_trend,
    average_daily_spending,
    percentage_of_total,
    filter_transactions,
)
from alerts import evaluate_rules, detect_consecutive_overspend, detect_uncategorized
from test_generator import generate_transactions, generate_sample_rules

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = "data"
TRANSACTIONS_FILE = f"{DATA_DIR}/transactions.json"
RULES_FILE = f"{DATA_DIR}/budget_rules.json"
CATEGORIES_FILE = f"{DATA_DIR}/categories.txt"


class BudgetAssistant:
    """
    Encapsulates the application state and menu logic.
    """

    def __init__(self):
        """Load persisted data or initialise empty structures."""
        self.transactions: List[Transaction] = load_transactions(TRANSACTIONS_FILE)
        self.rules: List[BudgetRule] = load_budget_rules(RULES_FILE)
        self.categories: List[str] = load_categories(CATEGORIES_FILE)
        self._next_txn_id = self._compute_next_txn_id()
        self._next_rule_id = self._compute_next_rule_id()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compute_next_txn_id(self) -> int:
        """Return the next available transaction ID (max + 1, or 1)."""
        if not self.transactions:
            return 1
        return max(t.txn_id for t in self.transactions) + 1

    def _compute_next_rule_id(self) -> int:
        """Return the next available rule ID (max + 1, or 1)."""
        if not self.rules:
            return 1
        return max(r.rule_id for r in self.rules) + 1

    def _save_all(self) -> None:
        """Persist current state to disk."""
        save_transactions(TRANSACTIONS_FILE, self.transactions)
        save_budget_rules(RULES_FILE, self.rules)
        save_categories(CATEGORIES_FILE, self.categories)

    def _read_date(self, prompt: str, allow_empty: bool = False) -> date:
        """
        Prompt the user for a date string and parse it.

        Args:
            prompt: Text shown to the user.
            allow_empty: If True and user presses Enter, return None.

        Returns:
            A date object, or None when allow_empty is True and input is blank.
        """
        while True:
            raw = input(prompt).strip()
            if not raw:
                if allow_empty:
                    return None
                print("Date is required. Please use YYYY-MM-DD format.")
                continue
            try:
                return date.fromisoformat(raw)
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD (e.g., 2025-04-27).")

    def _read_float(self, prompt: str, min_value: float = 0.0) -> float:
        """Prompt the user for a non-negative float value."""
        while True:
            raw = input(prompt).strip()
            try:
                val = float(raw)
                if val < min_value:
                    print(f"Value must be at least {min_value}.")
                    continue
                return val
            except ValueError:
                print("Invalid number. Please enter a valid decimal value.")

    def _read_category(self, prompt: str) -> str:
        """Prompt the user to pick an existing category or type a new one."""
        print("Available categories:", ", ".join(self.categories))
        while True:
            raw = input(prompt).strip().title()
            if raw:
                return raw
            print("Category cannot be empty.")

    def _pause(self) -> None:
        """Wait for user to press Enter before continuing."""
        input("\nPress Enter to return to the menu...")

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------
    def add_transaction(self) -> None:
        """Interactive workflow to add a new transaction."""
        print("\n--- Add New Transaction ---")
        txn_date = self._read_date("Date (YYYY-MM-DD): ")
        amount = self._read_float("Amount: ")
        category = self._read_category("Category: ")
        description = input("Description: ").strip()
        notes = input("Notes (optional): ").strip() or None

        txn = Transaction(
            txn_id=self._next_txn_id,
            date=txn_date,
            amount=amount,
            category=category,
            description=description,
            notes=notes,
        )
        self.transactions.append(txn)
        self._next_txn_id += 1
        self._save_all()
        print(f"Transaction added successfully: {txn}")

    def view_transactions(self) -> None:
        """Display all transactions, optionally filtered."""
        print("\n--- View Transactions ---")
        print("Leave filters empty to show all.\n")

        start = self._read_date("Start date (YYYY-MM-DD, optional): ", allow_empty=True)
        end = self._read_date("End date (YYYY-MM-DD, optional): ", allow_empty=True)
        cat = input("Category filter (optional): ").strip().title() or None
        if cat == "":
            cat = None

        filtered = filter_transactions(self.transactions, start_date=start, end_date=end, category=cat)

        if not filtered:
            print("No transactions match the given filters.")
            return

        print(f"\nShowing {len(filtered)} transaction(s):\n")
        for t in filtered:
            print(t)

    def view_summaries(self) -> None:
        """Show comprehensive spending summaries."""
        print("\n--- Spending Summaries ---")
        if not self.transactions:
            print("No transactions recorded yet.")
            return

        print(f"\nGrand Total: ${total_spending(self.transactions):,.2f}")
        print(f"Average Daily: ${average_daily_spending(self.transactions):,.2f}")

        print("\n--- By Category ---")
        by_cat = total_by_category(self.transactions)
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = percentage_of_total(self.transactions, cat)
            print(f"  {cat:<15} ${amt:>10,.2f}  ({pct:5.1f}%)")

        print("\n--- Top 3 Categories ---")
        for rank, (cat, amt) in enumerate(top_categories(self.transactions, n=3), start=1):
            print(f"  {rank}. {cat}: ${amt:,.2f}")

        print("\n--- Monthly Totals ---")
        monthly = total_by_period(self.transactions, period="monthly")
        for m, amt in sorted(monthly.items()):
            print(f"  {m}: ${amt:,.2f}")

        print("\n--- 7-Day Trend (ending today) ---")
        trend = spending_trend(self.transactions, days=7)
        for d, amt in trend.items():
            print(f"  {d}: ${amt:,.2f}")

    def manage_budget_rules(self) -> None:
        """Sub-menu for adding, listing, and deleting budget rules."""
        while True:
            print("\n--- Manage Budget Rules ---")
            print("1. List existing rules")
            print("2. Add a new rule")
            print("3. Delete a rule")
            print("4. Return to main menu")
            choice = input("Choice: ").strip()

            if choice == "1":
                if not self.rules:
                    print("No budget rules configured.")
                else:
                    for r in self.rules:
                        print(r)

            elif choice == "2":
                print("\n--- Add Rule ---")
                print("Categories:", ", ".join(self.categories), "or * for all")
                cat = input("Category (or *): ").strip().title()
                if cat == "":
                    cat = "*"
                period = input("Period (daily/weekly/monthly/yearly): ").strip().lower()
                if period not in {"daily", "weekly", "monthly", "yearly"}:
                    print("Invalid period. Rule cancelled.")
                    continue
                threshold = self._read_float("Threshold amount (or percentage): ")
                alert_type = input("Alert type (cap/percentage): ").strip().lower()
                if alert_type not in {"cap", "percentage"}:
                    print("Invalid type. Rule cancelled.")
                    continue
                rule = BudgetRule(
                    rule_id=self._next_rule_id,
                    category=cat,
                    period=period,
                    threshold=threshold,
                    alert_type=alert_type,
                )
                self.rules.append(rule)
                self._next_rule_id += 1
                self._save_all()
                print(f"Rule added: {rule}")

            elif choice == "3":
                if not self.rules:
                    print("No rules to delete.")
                    continue
                rid = input("Enter rule ID to delete: ").strip()
                try:
                    rid_int = int(rid)
                    before = len(self.rules)
                    self.rules = [r for r in self.rules if r.rule_id != rid_int]
                    if len(self.rules) < before:
                        self._save_all()
                        print("Rule deleted.")
                    else:
                        print("Rule ID not found.")
                except ValueError:
                    print("Invalid ID.")

            elif choice == "4":
                break
            else:
                print("Invalid choice.")

    def run_alerts(self) -> None:
        """Evaluate all configured rules and extra heuristics, then display alerts."""
        print("\n--- Running Budget Alerts ---")
        if not self.transactions:
            print("No transactions recorded — nothing to evaluate.")
            return
        if not self.rules:
            print("No budget rules configured.")

        alerts = evaluate_rules(self.transactions, self.rules)
        if alerts:
            print("\nRule-based alerts:")
            for a in alerts:
                print("  ", a)
        else:
            print("\nNo rule-based alerts triggered.")

        # Extra heuristic: detect consecutive overspend on Food (daily cap 50)
        food_alerts = detect_consecutive_overspend(
            self.transactions, category="Food", threshold=50.0, min_days=3
        )
        if food_alerts:
            print("\nConsecutive overspend alerts:")
            for a in food_alerts:
                print("  ", a)
        else:
            print("No consecutive overspend detected.")

        # Extra heuristic: uncategorized warnings
        uncategorized = detect_uncategorized(self.transactions)
        if uncategorized:
            print("\nUncategorized warnings:")
            for a in uncategorized:
                print("  ", a)
        else:
            print("No uncategorized transactions.")

    def manage_categories(self) -> None:
        """Allow user to view or reset the category list."""
        print("\n--- Manage Categories ---")
        print("Current categories:")
        for idx, cat in enumerate(self.categories, start=1):
            print(f"  {idx}. {cat}")
        print("\n1. Reset to defaults")
        print("2. Return")
        choice = input("Choice: ").strip()
        if choice == "1":
            self.categories = DEFAULT_CATEGORIES.copy()
            self._save_all()
            print("Categories reset to defaults.")

    def load_demo_data(self) -> None:
        """Populate the system with synthetic test data for quick evaluation."""
        print("\n--- Load Demo Data ---")
        count = input("How many transactions to generate? (default 50): ").strip()
        try:
            count = int(count) if count else 50
        except ValueError:
            count = 50

        print("Generating transactions...")
        new_txns = generate_transactions(count=count, seed=42)
        # Offset IDs so they do not clash with existing data
        for t in new_txns:
            t.txn_id = self._next_txn_id
            self._next_txn_id += 1
            self.transactions.append(t)

        if not self.rules:
            self.rules = generate_sample_rules()
            self._next_rule_id = max(r.rule_id for r in self.rules) + 1

        self._save_all()
        print(f"{count} transactions and default rules loaded.")

    def export_data(self) -> None:
        """Explicitly trigger a save of all in-memory data to disk."""
        self._save_all()
        print("All data saved successfully.")

    # ------------------------------------------------------------------
    # Main menu loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Display the main menu and dispatch to handlers."""
        print("=" * 60)
        print("  COMP1110 — Personal Budget and Spending Assistant")
        print("  Group C09 — Text-based Interactive System")
        print("=" * 60)

        while True:
            print("\n----------- Main Menu -----------")
            print("1.  Add Transaction")
            print("2.  View / Filter Transactions")
            print("3.  Spending Summaries")
            print("4.  Manage Budget Rules")
            print("5.  Run Alerts")
            print("6.  Manage Categories")
            print("7.  Load Demo Data")
            print("8.  Save Data")
            print("0.  Exit")
            print("---------------------------------")
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.add_transaction()
            elif choice == "2":
                self.view_transactions()
                self._pause()
            elif choice == "3":
                self.view_summaries()
                self._pause()
            elif choice == "4":
                self.manage_budget_rules()
            elif choice == "5":
                self.run_alerts()
                self._pause()
            elif choice == "6":
                self.manage_categories()
            elif choice == "7":
                self.load_demo_data()
            elif choice == "8":
                self.export_data()
            elif choice == "0":
                self._save_all()
                print("Data saved. Goodbye!")
                sys.exit(0)
            else:
                print("Invalid choice. Please enter a number from 0 to 8.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = BudgetAssistant()
    app.run()
