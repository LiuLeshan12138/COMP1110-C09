#!/usr/bin/env python3
"""
COMP1110 Project — Personal Budget and Spending Assistant
Module: gui_web.py
Description: Web-based graphical user interface using Flask. Provides
             browser-accessible pages for transaction management,
             summaries, budget rules, alerts, and case-study loading.
             This is an OPTIONAL frontend; the text-based main.py
             remains the primary required interface.
Author: Group C09
"""

import json
import sys
from datetime import date
from pathlib import Path

from flask import Flask, render_template_string, request, redirect, url_for, flash

# Ensure sibling modules are importable
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
# Flask setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "comp1110-budget-assistant-secret-key"

DATA_DIR = Path("data")
TRANSACTIONS_FILE = DATA_DIR / "transactions.json"
RULES_FILE = DATA_DIR / "budget_rules.json"
CATEGORIES_FILE = DATA_DIR / "categories.txt"

# ---------------------------------------------------------------------------
# In-memory state (loaded from disk on every request to stay simple)
# ---------------------------------------------------------------------------

def _load_state():
    """Return current transactions, rules, and categories from disk."""
    return (
        load_transactions(str(TRANSACTIONS_FILE)),
        load_budget_rules(str(RULES_FILE)),
        load_categories(str(CATEGORIES_FILE)),
    )


def _save_state(transactions, rules, categories):
    """Persist current state to JSON/text files."""
    save_transactions(str(TRANSACTIONS_FILE), transactions)
    save_budget_rules(str(RULES_FILE), rules)
    save_categories(str(CATEGORIES_FILE), categories)


def _next_txn_id(transactions):
    return max((t.txn_id for t in transactions), default=0) + 1


def _next_rule_id(rules):
    return max((r.rule_id for r in rules), default=0) + 1


# ---------------------------------------------------------------------------
# HTML base template (embedded to avoid template folder dependency)
# ---------------------------------------------------------------------------
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMP1110 Budget Assistant</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f4f6f8;
            color: #333;
            line-height: 1.6;
        }
        header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        header h1 { font-size: 1.3rem; }
        nav a {
            color: #ecf0f1;
            text-decoration: none;
            margin-left: 1.5rem;
            font-size: 0.95rem;
        }
        nav a:hover { color: #1abc9c; }
        .container {
            max-width: 1000px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        }
        .card h2 {
            font-size: 1.1rem;
            color: #2c3e50;
            margin-bottom: 1rem;
            border-bottom: 2px solid #1abc9c;
            padding-bottom: 0.4rem;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }
        th, td {
            text-align: left;
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid #e0e0e0;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }
        tr:hover { background: #f8f9fa; }
        .form-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 0.8rem;
            flex-wrap: wrap;
        }
        .form-row label {
            display: block;
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.2rem;
        }
        input, select {
            padding: 0.4rem 0.6rem;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 0.9rem;
            min-width: 140px;
        }
        button, .btn {
            padding: 0.5rem 1rem;
            background: #1abc9c;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            font-size: 0.9rem;
            display: inline-block;
        }
        button:hover, .btn:hover { background: #16a085; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-secondary { background: #7f8c8d; }
        .btn-secondary:hover { background: #6c7a7d; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1rem;
        }
        .stat-box {
            background: #ecf0f1;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }
        .stat-box .value {
            font-size: 1.4rem;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-box .label {
            font-size: 0.8rem;
            color: #777;
            margin-top: 0.3rem;
        }
        .alert-box {
            background: #ffebee;
            border-left: 4px solid #e74c3c;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem;
            border-radius: 4px;
            color: #c0392b;
        }
        .success-box {
            background: #e8f5e9;
            border-left: 4px solid #27ae60;
            padding: 0.8rem 1rem;
            margin-bottom: 0.6rem;
            border-radius: 4px;
            color: #2e7d32;
        }
        .case-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
        }
        .case-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
        }
        .case-card h3 {
            font-size: 1rem;
            margin-bottom: 0.5rem;
            color: #2c3e50;
        }
        .case-card p {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.8rem;
        }
    </style>
</head>
<body>
    <header>
        <h1>COMP1110 — Budget Assistant (Group C09)</h1>
        <nav>
            <a href="{{ url_for('index') }}">Dashboard</a>
            <a href="{{ url_for('transactions_page') }}">Transactions</a>
            <a href="{{ url_for('add_transaction_page') }}">Add</a>
            <a href="{{ url_for('summaries_page') }}">Summaries</a>
            <a href="{{ url_for('rules_page') }}">Rules</a>
            <a href="{{ url_for('alerts_page') }}">Alerts</a>
            <a href="{{ url_for('cases_page') }}">Case Studies</a>
        </nav>
    </header>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="{% if category == 'error' %}alert-box{% else %}success-box{% endif %}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Dashboard landing page showing key metrics."""
    transactions, rules, categories = _load_state()
    total = total_spending(transactions)
    avg = average_daily_spending(transactions)
    top3 = top_categories(transactions, n=3)

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Dashboard Overview</h2>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="value">{{ total }}</div>
                <div class="label">Total Spending</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ count }}</div>
                <div class="label">Transactions</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ avg }}</div>
                <div class="label">Avg Daily</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ rules_count }}</div>
                <div class="label">Budget Rules</div>
            </div>
        </div>
    </div>
    <div class="card">
        <h2>Top 3 Categories</h2>
        <table>
            <tr><th>Rank</th><th>Category</th><th>Amount</th></tr>
            {% for rank, (cat, amt) in enumerate(top3, start=1) %}
            <tr><td>{{ rank }}</td><td>{{ cat }}</td><td>${{ "%.2f"|format(amt) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h2>Quick Actions</h2>
        <a class="btn" href="{{ url_for('add_transaction_page') }}">+ Add Transaction</a>
        <a class="btn btn-secondary" href="{{ url_for('cases_page') }}" style="margin-left:0.5rem;">Load Case Study</a>
        <a class="btn btn-secondary" href="{{ url_for('alerts_page') }}" style="margin-left:0.5rem;">Run Alerts</a>
    </div>
    {% endblock %}
    """
    return render_template_string(
        BASE_TEMPLATE + html,
        total=f"${total:,.2f}" if transactions else "$0.00",
        count=len(transactions),
        avg=f"${avg:,.2f}" if transactions else "$0.00",
        rules_count=len(rules),
        top3=top3,
        enumerate=enumerate,
    )


@app.route("/transactions")
def transactions_page():
    """Paginated/filtered transaction list."""
    transactions, _, _ = _load_state()
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    cat = request.args.get("category", "").strip()

    start_date = date.fromisoformat(start) if start else None
    end_date = date.fromisoformat(end) if end else None
    category = cat if cat else None

    filtered = filter_transactions(transactions, start_date=start_date, end_date=end_date, category=category)

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>All Transactions ({{ filtered|length }} shown)</h2>
        <form method="get" action="{{ url_for('transactions_page') }}">
            <div class="form-row">
                <div>
                    <label>Start Date</label>
                    <input type="text" name="start" placeholder="YYYY-MM-DD" value="{{ start }}">
                </div>
                <div>
                    <label>End Date</label>
                    <input type="text" name="end" placeholder="YYYY-MM-DD" value="{{ end }}">
                </div>
                <div>
                    <label>Category</label>
                    <input type="text" name="category" placeholder="e.g. Food" value="{{ cat }}">
                </div>
                <div style="align-self:flex-end;">
                    <button type="submit">Filter</button>
                    <a class="btn btn-secondary" href="{{ url_for('transactions_page') }}">Clear</a>
                </div>
            </div>
        </form>
        <table>
            <tr><th>ID</th><th>Date</th><th>Amount</th><th>Category</th><th>Description</th><th>Action</th></tr>
            {% for t in filtered %}
            <tr>
                <td>{{ t.txn_id }}</td>
                <td>{{ t.date.isoformat() }}</td>
                <td>${{ "%.2f"|format(t.amount) }}</td>
                <td>{{ t.category }}</td>
                <td>{{ t.description }}</td>
                <td><a class="btn btn-danger" href="{{ url_for('delete_transaction', txn_id=t.txn_id) }}" onclick="return confirm('Delete transaction {{ t.txn_id }}?')">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + html, filtered=filtered, start=start, end=end, cat=cat)


@app.route("/transactions/delete/<int:txn_id>")
def delete_transaction(txn_id):
    """Delete a single transaction by ID."""
    transactions, rules, categories = _load_state()
    transactions = [t for t in transactions if t.txn_id != txn_id]
    _save_state(transactions, rules, categories)
    flash(f"Transaction {txn_id} deleted.", "success")
    return redirect(url_for("transactions_page"))


@app.route("/transactions/add", methods=["GET", "POST"])
def add_transaction_page():
    """Form for adding a new transaction."""
    transactions, rules, categories = _load_state()

    if request.method == "POST":
        date_str = request.form.get("date", "").strip()
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip().title()
        description = request.form.get("description", "").strip()
        notes = request.form.get("notes", "").strip() or None

        try:
            txn_date = date.fromisoformat(date_str)
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "error")
            return redirect(url_for("add_transaction_page"))

        try:
            amount = float(amount_str)
            if amount < 0:
                raise ValueError
        except ValueError:
            flash("Amount must be a non-negative number.", "error")
            return redirect(url_for("add_transaction_page"))

        if not category:
            flash("Category cannot be empty.", "error")
            return redirect(url_for("add_transaction_page"))

        txn = Transaction(
            txn_id=_next_txn_id(transactions),
            date=txn_date,
            amount=amount,
            category=category,
            description=description,
            notes=notes,
        )
        transactions.append(txn)
        _save_state(transactions, rules, categories)
        flash(f"Transaction added: {txn.description} (${amount:,.2f})", "success")
        return redirect(url_for("add_transaction_page"))

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Add New Transaction</h2>
        <form method="post">
            <div class="form-row">
                <div>
                    <label>Date (YYYY-MM-DD)</label>
                    <input type="text" name="date" value="{{ today }}" required>
                </div>
                <div>
                    <label>Amount</label>
                    <input type="text" name="amount" placeholder="0.00" required>
                </div>
                <div>
                    <label>Category</label>
                    <input type="text" name="category" list="cats" placeholder="e.g. Food" required>
                    <datalist id="cats">
                        {% for c in categories %}<option value="{{ c }}">{% endfor %}
                    </datalist>
                </div>
            </div>
            <div class="form-row">
                <div style="flex:1;">
                    <label>Description</label>
                    <input type="text" name="description" placeholder="Short description" style="width:100%;" required>
                </div>
            </div>
            <div class="form-row">
                <div style="flex:1;">
                    <label>Notes (optional)</label>
                    <input type="text" name="notes" placeholder="Extra details" style="width:100%;">
                </div>
            </div>
            <button type="submit">Add Transaction</button>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + html, today=date.today().isoformat(), categories=categories)


@app.route("/summaries")
def summaries_page():
    """Display full spending summaries and trends."""
    transactions, _, _ = _load_state()

    if not transactions:
        return render_template_string(BASE_TEMPLATE + """
        {% extends "base" %}{% block content %}
        <div class="card"><h2>Summaries</h2><p>No transactions recorded yet.</p></div>
        {% endblock %}"""), 200

    total = total_spending(transactions)
    avg = average_daily_spending(transactions)
    by_cat = total_by_category(transactions)
    top3 = top_categories(transactions, n=3)
    monthly = total_by_period(transactions, "monthly")
    weekly = total_by_period(transactions, "weekly")
    trend7 = spending_trend(transactions, days=7)

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Overall Statistics</h2>
        <div class="stats-grid">
            <div class="stat-box"><div class="value">${{ "%.2f"|format(total) }}</div><div class="label">Grand Total</div></div>
            <div class="stat-box"><div class="value">${{ "%.2f"|format(avg) }}</div><div class="label">Avg Daily</div></div>
            <div class="stat-box"><div class="value">{{ count }}</div><div class="label">Transactions</div></div>
        </div>
    </div>
    <div class="card">
        <h2>By Category</h2>
        <table>
            <tr><th>Category</th><th>Amount</th><th>Share</th></tr>
            {% for cat, amt in by_cat|dictsort(by='value', reverse=true) %}
            <tr><td>{{ cat }}</td><td>${{ "%.2f"|format(amt) }}</td><td>{{ "%.1f"|format(pct_total[cat]) }}%</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h2>Top 3 Categories</h2>
        <table>
            <tr><th>Rank</th><th>Category</th><th>Amount</th></tr>
            {% for rank, (cat, amt) in enumerate(top3, start=1) %}
            <tr><td>{{ rank }}</td><td>{{ cat }}</td><td>${{ "%.2f"|format(amt) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h2>Monthly Totals</h2>
        <table>
            <tr><th>Month</th><th>Amount</th></tr>
            {% for m, amt in monthly.items()|sort %}
            <tr><td>{{ m }}</td><td>${{ "%.2f"|format(amt) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h2>7-Day Trend</h2>
        <table>
            <tr><th>Date</th><th>Amount</th></tr>
            {% for d, amt in trend7.items() %}
            <tr><td>{{ d }}</td><td>${{ "%.2f"|format(amt) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """
    pct_total = {cat: percentage_of_total(transactions, cat) for cat in by_cat}
    return render_template_string(BASE_TEMPLATE + html, total=total, avg=avg, count=len(transactions),
                                   by_cat=by_cat, top3=top3, monthly=monthly, trend7=trend7,
                                   pct_total=pct_total, enumerate=enumerate)


@app.route("/rules", methods=["GET", "POST"])
def rules_page():
    """Budget rules management page."""
    transactions, rules, categories = _load_state()

    if request.method == "POST":
        cat = request.form.get("category", "").strip()
        period = request.form.get("period", "").strip()
        try:
            threshold = float(request.form.get("threshold", "").strip())
        except ValueError:
            flash("Threshold must be a number.", "error")
            return redirect(url_for("rules_page"))
        alert_type = request.form.get("alert_type", "").strip()

        try:
            rule = BudgetRule(
                rule_id=_next_rule_id(rules),
                category=cat,
                period=period,
                threshold=threshold,
                alert_type=alert_type,
            )
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("rules_page"))

        rules.append(rule)
        _save_state(transactions, rules, categories)
        flash(f"Rule added: {rule}", "success")
        return redirect(url_for("rules_page"))

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Existing Budget Rules ({{ rules|length }})</h2>
        <table>
            <tr><th>ID</th><th>Category</th><th>Period</th><th>Threshold</th><th>Type</th><th>Action</th></tr>
            {% for r in rules %}
            <tr>
                <td>{{ r.rule_id }}</td>
                <td>{{ r.category }}</td>
                <td>{{ r.period }}</td>
                <td>{{ "%.2f"|format(r.threshold) }}</td>
                <td>{{ r.alert_type }}</td>
                <td><a class="btn btn-danger" href="{{ url_for('delete_rule', rule_id=r.rule_id) }}">Delete</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <div class="card">
        <h2>Add New Rule</h2>
        <form method="post">
            <div class="form-row">
                <div>
                    <label>Category (or *)</label>
                    <input type="text" name="category" placeholder="Food or *" required>
                </div>
                <div>
                    <label>Period</label>
                    <select name="period" required>
                        <option value="daily">daily</option>
                        <option value="weekly">weekly</option>
                        <option value="monthly" selected>monthly</option>
                        <option value="yearly">yearly</option>
                    </select>
                </div>
                <div>
                    <label>Threshold</label>
                    <input type="text" name="threshold" placeholder="50.0" required>
                </div>
                <div>
                    <label>Alert Type</label>
                    <select name="alert_type" required>
                        <option value="cap" selected>cap</option>
                        <option value="percentage">percentage</option>
                    </select>
                </div>
                <div style="align-self:flex-end;">
                    <button type="submit">Add Rule</button>
                </div>
            </div>
        </form>
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + html, rules=rules)


@app.route("/rules/delete/<int:rule_id>")
def delete_rule(rule_id):
    """Delete a budget rule by ID."""
    transactions, rules, categories = _load_state()
    rules = [r for r in rules if r.rule_id != rule_id]
    _save_state(transactions, rules, categories)
    flash(f"Rule {rule_id} deleted.", "success")
    return redirect(url_for("rules_page"))


@app.route("/alerts")
def alerts_page():
    """Run and display all budget alerts."""
    transactions, rules, _ = _load_state()

    if not transactions:
        return render_template_string(BASE_TEMPLATE + """
        {% extends "base" %}{% block content %}
        <div class="card"><h2>Alerts</h2><p>No transactions to evaluate.</p></div>
        {% endblock %}"""), 200

    ref = max(t.date for t in transactions)
    rule_alerts = evaluate_rules(transactions, rules, reference_date=ref)
    food_streak = detect_consecutive_overspend(transactions, "Food", 50.0, min_days=3)
    uncategorized = detect_uncategorized(transactions)

    all_alerts = rule_alerts + food_streak + uncategorized

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Alert Evaluation Results</h2>
        <p>Reference date: {{ ref }}</p>
        {% if alerts %}
            {% for a in alerts %}
            <div class="alert-box">{{ a }}</div>
            {% endfor %}
        {% else %}
            <div class="success-box">No alerts triggered. Your spending is within budget!</div>
        {% endif %}
    </div>
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + html, alerts=all_alerts, ref=ref.isoformat())


@app.route("/cases", methods=["GET", "POST"])
def cases_page():
    """Load and preview case study scenarios."""
    transactions, rules, categories = _load_state()

    cases = [
        ("Case 1: Daily Food Budget HK$50", "case1_daily_food",
         "A student tries to keep daily food spending under HK$50. Demonstrates daily category caps and consecutive overspend detection."),
        ("Case 2: Monthly Transport Tracking", "case2_transport",
         "Tracks MTR, bus, taxi and ferry costs against a HK$500 monthly transport budget. Shows monthly cap and percentage alerts."),
        ("Case 3: Subscription Creep Detection", "case3_subscriptions",
         "Follows a student adding Netflix, Spotify, gym, Adobe and VPN subscriptions over 4 months. Illustrates creeping recurring costs."),
        ("Case 4: Consecutive Overspend Pattern", "case4_overspend",
         "A student overspends on food for 5 straight days due to social dining and stress. Demonstrates streak-based heuristic alerts."),
        ("Case 5: Entertainment Percentage Alert", "case5_entertainment",
         "A student with balanced categories but entertainment exceeds 20% of total spending. Shows percentage-type budget rules."),
        ("Case 6: Zero Spending Edge Case", "case6_zero_spending",
         "A holiday week with $0 spending and only free activities. Tests zero-division guards and empty-dataset handling."),
    ]

    loaded_info = None
    if request.method == "POST":
        folder = request.form.get("folder", "").strip()
        base = Path(__file__).parent / "case_studies" / folder
        try:
            txns = load_transactions(str(base / "transactions.json"))
            rls = load_budget_rules(str(base / "budget_rules.json"))
            transactions = txns
            rules = rls
            _save_state(transactions, rules, categories)
            ref = max(t.date for t in transactions) if transactions else date.today()
            alerts = evaluate_rules(transactions, rules, reference_date=ref)
            loaded_info = {
                "folder": folder,
                "txns": len(txns),
                "rules": len(rls),
                "alerts": alerts,
            }
            flash(f"Loaded {folder}: {len(txns)} transactions, {len(rls)} rules.", "success")
        except Exception as exc:
            flash(f"Failed to load case study: {exc}", "error")

    html = """
    {% extends "base" %}
    {% block content %}
    <div class="card">
        <h2>Case Studies</h2>
        <p>Click "Load" to import a pre-built scenario into the live system.</p>
        <div class="case-grid">
            {% for title, folder, desc in cases %}
            <div class="case-card">
                <h3>{{ title }}</h3>
                <p>{{ desc }}</p>
                <form method="post" action="{{ url_for('cases_page') }}">
                    <input type="hidden" name="folder" value="{{ folder }}">
                    <button type="submit">Load Scenario</button>
                </form>
            </div>
            {% endfor %}
        </div>
    </div>
    {% if loaded %}
    <div class="card">
        <h2>Loaded: {{ loaded.folder }}</h2>
        <p>Transactions: {{ loaded.txns }} | Rules: {{ loaded.rules }}</p>
        {% if loaded.alerts %}
            <h3 style="margin-top:1rem;">Alerts Triggered:</h3>
            {% for a in loaded.alerts %}
            <div class="alert-box">{{ a }}</div>
            {% endfor %}
        {% else %}
            <div class="success-box">No alerts for this scenario.</div>
        {% endif %}
    </div>
    {% endif %}
    {% endblock %}
    """
    return render_template_string(BASE_TEMPLATE + html, cases=cases, loaded=loaded_info)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Starting Budget Assistant Web GUI...")
    print("Open your browser and navigate to http://127.0.0.1:5000/")
    app.run(debug=False, host="127.0.0.1", port=5000)
