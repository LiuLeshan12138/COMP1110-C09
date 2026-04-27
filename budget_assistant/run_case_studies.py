#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: run_case_studies.py
Description: Batch runner for all six project case studies. Each case
             loads its own transaction file and budget rules, prints
             summaries, and evaluates alerts. Results are written to
             text files for easy inclusion in the final report.
Author: Group C09
"""

import sys
from datetime import date
from pathlib import Path

# Ensure main modules are importable
sys.path.insert(0, str(Path(__file__).parent))

from models import Transaction, BudgetRule
from storage import load_transactions, load_budget_rules
from statistics import (
    total_spending,
    total_by_category,
    total_by_period,
    top_categories,
    spending_trend,
    average_daily_spending,
    percentage_of_total,
)
from alerts import evaluate_rules, detect_consecutive_overspend, detect_uncategorized


CASES = [
    ("case1_daily_food", "Case Study 1 — Daily Food Budget HK$50"),
    ("case2_transport", "Case Study 2 — Monthly Transport Tracking"),
    ("case3_subscriptions", "Case Study 3 — Subscription Creep Detection"),
    ("case4_overspend", "Case Study 4 — Consecutive Overspend Pattern"),
    ("case5_entertainment", "Case Study 5 — Entertainment Percentage Alert"),
    ("case6_zero_spending", "Case Study 6 — Zero Spending Edge Case"),
]


def run_case(case_dir: str, title: str) -> str:
    """
    Load case data, compute statistics, evaluate alerts, and format
    everything into a single report string.
    """
    base = Path(__file__).parent / "case_studies" / case_dir
    txns = load_transactions(str(base / "transactions.json"))
    rules = load_budget_rules(str(base / "budget_rules.json"))

    lines = []
    lines.append("=" * 70)
    lines.append(title)
    lines.append("=" * 70)
    lines.append("")

    # --- Raw data preview ---
    lines.append("--- Transactions ---")
    if txns:
        for t in txns:
            lines.append(str(t))
    else:
        lines.append("(No transactions)")
    lines.append("")

    lines.append("--- Budget Rules ---")
    if rules:
        for r in rules:
            lines.append(str(r))
    else:
        lines.append("(No rules)")
    lines.append("")

    # --- Summaries ---
    if txns:
        lines.append("--- Spending Summaries ---")
        lines.append(f"Grand Total:        ${total_spending(txns):,.2f}")
        lines.append(f"Average Daily:      ${average_daily_spending(txns):,.2f}")
        lines.append("")

        lines.append("By Category:")
        by_cat = total_by_category(txns)
        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = percentage_of_total(txns, cat)
            lines.append(f"  {cat:<18} ${amt:>10,.2f}  ({pct:5.1f}%)")
        lines.append("")

        lines.append("Top 3 Categories:")
        for rank, (cat, amt) in enumerate(top_categories(txns, n=3), start=1):
            lines.append(f"  {rank}. {cat}: ${amt:,.2f}")
        lines.append("")

        lines.append("Monthly Totals:")
        for m, amt in sorted(total_by_period(txns, "monthly").items()):
            lines.append(f"  {m}: ${amt:,.2f}")
        lines.append("")

        lines.append("Weekly Totals:")
        for w, amt in sorted(total_by_period(txns, "weekly").items()):
            lines.append(f"  {w}: ${amt:,.2f}")
        lines.append("")

        lines.append("7-Day Trend (last 7 days of data):")
        max_date = max(t.date for t in txns)
        trend = spending_trend(txns, days=7, end_date=max_date)
        for d, amt in trend.items():
            lines.append(f"  {d}: ${amt:,.2f}")
        lines.append("")
    else:
        lines.append("(No transactions — summaries unavailable)")
        lines.append("")

    # --- Alerts ---
    lines.append("--- Alert Evaluation ---")
    ref = max(t.date for t in txns) if txns else date.today()
    rule_alerts = evaluate_rules(txns, rules, reference_date=ref)
    if rule_alerts:
        for a in rule_alerts:
            lines.append(a)
    else:
        lines.append("No rule-based alerts triggered.")
    lines.append("")

    if txns:
        # Extra heuristic for consecutive overspend
        food_streak = detect_consecutive_overspend(txns, "Food", 50.0, min_days=3)
        if food_streak:
            lines.append("Consecutive overspend alerts:")
            for a in food_streak:
                lines.append(a)
            lines.append("")

        uncategorized = detect_uncategorized(txns)
        if uncategorized:
            for a in uncategorized:
                lines.append(a)
            lines.append("")

    lines.append("--- End of Case Study ---")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    """Run every case study and write combined output to a report file."""
    output_path = Path(__file__).parent / "case_studies" / "case_study_outputs.txt"
    all_reports = []

    for case_dir, title in CASES:
        print(f"Running {case_dir} ...")
        report = run_case(case_dir, title)
        all_reports.append(report)

    full_text = "\n".join(all_reports)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    print(f"\nAll case study outputs saved to: {output_path}")


if __name__ == "__main__":
    main()
