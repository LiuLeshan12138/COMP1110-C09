#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: gui_tkinter.py
Description: Desktop graphical user interface built with Python tkinter.
             Provides tabbed access to all core features: transaction
             management, summaries, budget rules, alerts, and case-study
             loading. Uses the same backend modules as main.py so all
             business logic is shared.
Author: Group C09
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import date
from pathlib import Path
import shutil
import sys

# Ensure sibling modules are importable when run directly
sys.path.insert(0, str(Path(__file__).parent))

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


class BudgetApp:
    """Main application class wrapping all tkinter widgets and logic."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("COMP1110 — Personal Budget and Spending Assistant (Group C09)")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        # Load persisted state
        self.transactions: list[Transaction] = load_transactions(TRANSACTIONS_FILE)
        self.rules: list[BudgetRule] = load_budget_rules(RULES_FILE)
        self.categories: list[str] = load_categories(CATEGORIES_FILE)
        self._next_txn_id = self._compute_next_txn_id()
        self._next_rule_id = self._compute_next_rule_id()

        # Build UI
        self._build_menu()
        self._build_notebook()
        self._refresh_all()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _compute_next_txn_id(self) -> int:
        if not self.transactions:
            return 1
        return max(t.txn_id for t in self.transactions) + 1

    def _compute_next_rule_id(self) -> int:
        if not self.rules:
            return 1
        return max(r.rule_id for r in self.rules) + 1

    def _save_all(self) -> None:
        save_transactions(TRANSACTIONS_FILE, self.transactions)
        save_budget_rules(RULES_FILE, self.rules)
        save_categories(CATEGORIES_FILE, self.categories)

    def _refresh_all(self) -> None:
        """Refresh every tab that displays data."""
        self._refresh_transactions_tab()
        self._refresh_summaries_tab()
        self._refresh_rules_tab()

    # ------------------------------------------------------------------
    # Menu bar
    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save All Data", command=self._save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        data_menu = tk.Menu(menubar, tearoff=0)
        data_menu.add_command(label="Generate Demo Data (50 txns)", command=self._load_demo_data)
        data_menu.add_command(label="Reset Categories to Default", command=self._reset_categories)
        menubar.add_cascade(label="Data", menu=data_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "COMP1110 — Personal Budget and Spending Assistant\n"
            "Group C09 | Topic A\n\n"
            "A text-based + GUI budgeting tool for university students.\n"
            "Built with Python 3 and tkinter.",
        )

    def _load_demo_data(self):
        new_txns = generate_transactions(count=50, seed=42)
        for t in new_txns:
            t.txn_id = self._next_txn_id
            self._next_txn_id += 1
            self.transactions.append(t)
        if not self.rules:
            self.rules = generate_sample_rules()
            self._next_rule_id = max(r.rule_id for r in self.rules) + 1
        self._save_all()
        self._refresh_all()
        messagebox.showinfo("Demo Data", "50 synthetic transactions loaded successfully.")

    def _reset_categories(self):
        self.categories = DEFAULT_CATEGORIES.copy()
        self._save_all()
        messagebox.showinfo("Categories", "Category list reset to defaults.")

    # ------------------------------------------------------------------
    # Notebook (tabs)
    # ------------------------------------------------------------------
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1 — Transactions
        self.tab_txns = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_txns, text="Transactions")
        self._build_transactions_tab()

        # Tab 2 — Add Transaction
        self.tab_add = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_add, text="Add Transaction")
        self._build_add_tab()

        # Tab 3 — Summaries
        self.tab_summary = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_summary, text="Summaries")
        self._build_summaries_tab()

        # Tab 4 — Budget Rules
        self.tab_rules = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_rules, text="Budget Rules")
        self._build_rules_tab()

        # Tab 5 — Alerts
        self.tab_alerts = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_alerts, text="Alerts")
        self._build_alerts_tab()

        # Tab 6 — Case Studies
        self.tab_cases = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_cases, text="Case Studies")
        self._build_cases_tab()

    # =================================================================
    # Tab 1 — Transactions (view / filter / delete)
    # =================================================================
    def _build_transactions_tab(self):
        # Filter frame
        filter_frame = ttk.LabelFrame(self.tab_txns, text="Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.filter_start = ttk.Entry(filter_frame, width=12)
        self.filter_start.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(filter_frame, text="End Date (YYYY-MM-DD):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.filter_end = ttk.Entry(filter_frame, width=12)
        self.filter_end.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.filter_cat = ttk.Combobox(filter_frame, values=["All"] + self.categories, width=12, state="readonly")
        self.filter_cat.set("All")
        self.filter_cat.grid(row=0, column=5, padx=5, pady=2)

        ttk.Button(filter_frame, text="Apply Filters", command=self._apply_txn_filters).grid(row=0, column=6, padx=10, pady=2)
        ttk.Button(filter_frame, text="Clear Filters", command=self._clear_txn_filters).grid(row=0, column=7, padx=5, pady=2)

        # Treeview
        cols = ("ID", "Date", "Amount", "Category", "Description")
        self.txn_tree = ttk.Treeview(self.tab_txns, columns=cols, show="headings", height=18)
        for c in cols:
            self.txn_tree.heading(c, text=c)
            self.txn_tree.column(c, width=120 if c == "Description" else 90)
        self.txn_tree.column("ID", width=50)
        self.txn_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbar
        sb = ttk.Scrollbar(self.txn_tree, orient=tk.VERTICAL, command=self.txn_tree.yview)
        self.txn_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Delete button
        btn_frame = ttk.Frame(self.tab_txns)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="Delete Selected Transaction", command=self._delete_selected_txn).pack(side=tk.LEFT, padx=5)
        ttk.Label(btn_frame, text=f"Total transactions: {len(self.transactions)}").pack(side=tk.RIGHT, padx=5)
        self.txn_count_label = ttk.Label(btn_frame, text="0 shown")
        self.txn_count_label.pack(side=tk.RIGHT, padx=5)

    def _refresh_transactions_tab(self):
        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
        for t in self.transactions:
            self.txn_tree.insert("", tk.END, values=(t.txn_id, t.date.isoformat(), f"${t.amount:,.2f}", t.category, t.description))
        self.txn_count_label.config(text=f"{len(self.transactions)} shown")

    def _apply_txn_filters(self):
        start_txt = self.filter_start.get().strip()
        end_txt = self.filter_end.get().strip()
        cat = self.filter_cat.get()

        start_date = date.fromisoformat(start_txt) if start_txt else None
        end_date = date.fromisoformat(end_txt) if end_txt else None
        category = None if cat == "All" else cat

        filtered = filter_transactions(self.transactions, start_date=start_date, end_date=end_date, category=category)

        for item in self.txn_tree.get_children():
            self.txn_tree.delete(item)
        for t in filtered:
            self.txn_tree.insert("", tk.END, values=(t.txn_id, t.date.isoformat(), f"${t.amount:,.2f}", t.category, t.description))
        self.txn_count_label.config(text=f"{len(filtered)} shown (filtered)")

    def _clear_txn_filters(self):
        self.filter_start.delete(0, tk.END)
        self.filter_end.delete(0, tk.END)
        self.filter_cat.set("All")
        self._refresh_transactions_tab()

    def _delete_selected_txn(self):
        selected = self.txn_tree.selection()
        if not selected:
            messagebox.showwarning("Delete", "Please select a transaction to delete.")
            return
        item = selected[0]
        txn_id = int(self.txn_tree.item(item, "values")[0])
        self.transactions = [t for t in self.transactions if t.txn_id != txn_id]
        self._save_all()
        self._refresh_all()
        messagebox.showinfo("Delete", f"Transaction {txn_id} deleted.")

    # =================================================================
    # Tab 2 — Add Transaction
    # =================================================================
    def _build_add_tab(self):
        frame = ttk.Frame(self.tab_add, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Add New Transaction", font=("Helvetica", 14, "bold")).pack(pady=10)

        form = ttk.Frame(frame)
        form.pack(pady=10)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.add_date = ttk.Entry(form, width=15)
        self.add_date.insert(0, date.today().isoformat())
        self.add_date.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Label(form, text="Amount:").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.add_amount = ttk.Entry(form, width=15)
        self.add_amount.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Label(form, text="Category:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.add_cat = ttk.Combobox(form, values=self.categories, width=15, state="normal")
        self.add_cat.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Label(form, text="Description:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.add_desc = ttk.Entry(form, width=40)
        self.add_desc.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Label(form, text="Notes (optional):").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        self.add_notes = ttk.Entry(form, width=40)
        self.add_notes.grid(row=4, column=1, pady=5, padx=5, sticky=tk.W)

        ttk.Button(frame, text="Add Transaction", command=self._add_transaction).pack(pady=15)

        self.add_status = ttk.Label(frame, text="", foreground="green")
        self.add_status.pack()

    def _add_transaction(self):
        try:
            txn_date = date.fromisoformat(self.add_date.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        try:
            amount = float(self.add_amount.get().strip())
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a non-negative number.")
            return

        category = self.add_cat.get().strip().title()
        if not category:
            messagebox.showerror("Error", "Category cannot be empty.")
            return

        description = self.add_desc.get().strip()
        notes = self.add_notes.get().strip() or None

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
        self._refresh_all()

        self.add_amount.delete(0, tk.END)
        self.add_desc.delete(0, tk.END)
        self.add_notes.delete(0, tk.END)
        self.add_status.config(text=f"Added: {txn}")

    # =================================================================
    # Tab 3 — Summaries
    # =================================================================
    def _build_summaries_tab(self):
        frame = ttk.Frame(self.tab_summary, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Spending Summaries", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=5)

        self.summary_text = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10))
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        sb = ttk.Scrollbar(self.summary_text, orient=tk.VERTICAL, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(frame, text="Refresh Summaries", command=self._refresh_summaries_tab).pack(anchor=tk.W, pady=5)

    def _refresh_summaries_tab(self):
        self.summary_text.delete("1.0", tk.END)
        if not self.transactions:
            self.summary_text.insert(tk.END, "No transactions recorded yet.\n")
            return

        lines = []
        lines.append(f"Grand Total:        ${total_spending(self.transactions):,.2f}\n")
        lines.append(f"Average Daily:      ${average_daily_spending(self.transactions):,.2f}\n")
        lines.append(f"Transaction Count:  {len(self.transactions)}\n")
        lines.append("\n--- By Category ---\n")
        by_cat = total_by_category(self.transactions)
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = percentage_of_total(self.transactions, cat)
            lines.append(f"  {cat:<15} ${amt:>10,.2f}  ({pct:5.1f}%)\n")

        lines.append("\n--- Top 3 Categories ---\n")
        for rank, (cat, amt) in enumerate(top_categories(self.transactions, n=3), start=1):
            lines.append(f"  {rank}. {cat}: ${amt:,.2f}\n")

        lines.append("\n--- Monthly Totals ---\n")
        for m, amt in sorted(total_by_period(self.transactions, "monthly").items()):
            lines.append(f"  {m}: ${amt:,.2f}\n")

        lines.append("\n--- Weekly Totals ---\n")
        for w, amt in sorted(total_by_period(self.transactions, "weekly").items()):
            lines.append(f"  {w}: ${amt:,.2f}\n")

        lines.append("\n--- 7-Day Trend ---\n")
        for d, amt in spending_trend(self.transactions, days=7).items():
            lines.append(f"  {d}: ${amt:,.2f}\n")

        lines.append("\n--- 30-Day Trend ---\n")
        for d, amt in spending_trend(self.transactions, days=30).items():
            lines.append(f"  {d}: ${amt:,.2f}\n")

        self.summary_text.insert(tk.END, "".join(lines))

    def _refresh_summaries_tab_wrapper(self):
        """Called by _refresh_all so summaries stay up to date."""
        self._refresh_summaries_tab()

    # =================================================================
    # Tab 4 — Budget Rules
    # =================================================================
    def _build_rules_tab(self):
        frame = ttk.Frame(self.tab_rules, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Budget Rules", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=5)

        # Existing rules list
        cols = ("ID", "Category", "Period", "Threshold", "Type")
        self.rules_tree = ttk.Treeview(frame, columns=cols, show="headings", height=8)
        for c in cols:
            self.rules_tree.heading(c, text=c)
            self.rules_tree.column(c, width=100)
        self.rules_tree.column("ID", width=50)
        self.rules_tree.pack(fill=tk.X, padx=5, pady=5)

        # Add rule form
        form = ttk.LabelFrame(frame, text="Add New Rule")
        form.pack(fill=tk.X, padx=5, pady=10)

        ttk.Label(form, text="Category (or * for all):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.rule_cat = ttk.Combobox(form, values=["*"] + self.categories, width=12, state="normal")
        self.rule_cat.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(form, text="Period:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.rule_period = ttk.Combobox(form, values=["daily", "weekly", "monthly", "yearly"], width=10, state="readonly")
        self.rule_period.set("daily")
        self.rule_period.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(form, text="Threshold:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.rule_threshold = ttk.Entry(form, width=12)
        self.rule_threshold.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(form, text="Alert Type:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.rule_type = ttk.Combobox(form, values=["cap", "percentage"], width=10, state="readonly")
        self.rule_type.set("cap")
        self.rule_type.grid(row=1, column=3, padx=5, pady=2)

        ttk.Button(form, text="Add Rule", command=self._add_rule).grid(row=1, column=4, padx=10, pady=2)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Delete Selected Rule", command=self._delete_selected_rule).pack(side=tk.LEFT, padx=5)

    def _refresh_rules_tab(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        for r in self.rules:
            self.rules_tree.insert("", tk.END, values=(r.rule_id, r.category, r.period, f"{r.threshold:,.2f}", r.alert_type))

    def _add_rule(self):
        cat = self.rule_cat.get().strip()
        if not cat:
            messagebox.showerror("Error", "Category cannot be empty. Use * for all.")
            return
        period = self.rule_period.get()
        try:
            threshold = float(self.rule_threshold.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Threshold must be a number.")
            return
        alert_type = self.rule_type.get()

        try:
            rule = BudgetRule(
                rule_id=self._next_rule_id,
                category=cat,
                period=period,
                threshold=threshold,
                alert_type=alert_type,
            )
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.rules.append(rule)
        self._next_rule_id += 1
        self._save_all()
        self._refresh_rules_tab()
        self.rule_threshold.delete(0, tk.END)
        messagebox.showinfo("Rule Added", str(rule))

    def _delete_selected_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showwarning("Delete", "Select a rule to delete.")
            return
        rid = int(self.rules_tree.item(selected[0], "values")[0])
        self.rules = [r for r in self.rules if r.rule_id != rid]
        self._save_all()
        self._refresh_rules_tab()

    # =================================================================
    # Tab 5 — Alerts
    # =================================================================
    def _build_alerts_tab(self):
        frame = ttk.Frame(self.tab_alerts, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Budget Alerts", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=5)
        ttk.Button(frame, text="Run Alert Evaluation", command=self._run_alerts).pack(anchor=tk.W, pady=5)

        self.alerts_text = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10), foreground="red")
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        sb = ttk.Scrollbar(self.alerts_text, orient=tk.VERTICAL, command=self.alerts_text.yview)
        self.alerts_text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _run_alerts(self):
        self.alerts_text.delete("1.0", tk.END)
        if not self.transactions:
            self.alerts_text.insert(tk.END, "No transactions to evaluate.\n")
            return

        ref = max(t.date for t in self.transactions) if self.transactions else date.today()
        alerts = evaluate_rules(self.transactions, self.rules, reference_date=ref)
        lines = []
        if alerts:
            lines.append("=== Rule-Based Alerts ===\n")
            for a in alerts:
                lines.append(a + "\n")
        else:
            lines.append("No rule-based alerts triggered.\n")

        food_streak = detect_consecutive_overspend(self.transactions, "Food", 50.0, min_days=3)
        if food_streak:
            lines.append("\n=== Consecutive Overspend Alerts ===\n")
            for a in food_streak:
                lines.append(a + "\n")

        uncategorized = detect_uncategorized(self.transactions)
        if uncategorized:
            lines.append("\n=== Uncategorized Warnings ===\n")
            for a in uncategorized:
                lines.append(a + "\n")

        self.alerts_text.insert(tk.END, "".join(lines))

    # =================================================================
    # Tab 6 — Case Studies
    # =================================================================
    def _build_cases_tab(self):
        frame = ttk.Frame(self.tab_cases, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Case Studies", font=("Helvetica", 14, "bold")).pack(anchor=tk.W, pady=5)
        ttk.Label(frame, text="Load a pre-built scenario to explore the system.", wraplength=600).pack(anchor=tk.W, pady=2)

        self.case_text = tk.Text(frame, wrap=tk.WORD, font=("Courier", 9))
        self.case_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)

        cases = [
            ("Case 1: Daily Food Budget", "case1_daily_food"),
            ("Case 2: Transport Monthly", "case2_transport"),
            ("Case 3: Subscription Creep", "case3_subscriptions"),
            ("Case 4: Consecutive Overspend", "case4_overspend"),
            ("Case 5: Entertainment %", "case5_entertainment"),
            ("Case 6: Zero Spending", "case6_zero_spending"),
        ]

        for label, folder in cases:
            ttk.Button(btn_frame, text=label, command=lambda f=folder: self._load_case(f)).pack(side=tk.LEFT, padx=3, pady=2)

    def _load_case(self, folder: str):
        base = Path(__file__).parent / "case_studies" / folder
        try:
            txns = load_transactions(str(base / "transactions.json"))
            rules = load_budget_rules(str(base / "budget_rules.json"))
            self.transactions = txns
            self.rules = rules
            self._next_txn_id = self._compute_next_txn_id()
            self._next_rule_id = self._compute_next_rule_id()
            self._save_all()
            self._refresh_all()

            # Auto-run alerts and show in case text
            ref = max(t.date for t in self.transactions) if self.transactions else date.today()
            alerts = evaluate_rules(self.transactions, self.rules, reference_date=ref)
            lines = [f"Loaded: {folder}\n", f"Transactions: {len(txns)} | Rules: {len(rules)}\n\n"]
            if alerts:
                lines.append("ALERTS:\n")
                for a in alerts:
                    lines.append(a + "\n")
            else:
                lines.append("No alerts triggered.\n")
            self.case_text.delete("1.0", tk.END)
            self.case_text.insert(tk.END, "".join(lines))
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load case study:\n{exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    root = tk.Tk()
    app = BudgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
