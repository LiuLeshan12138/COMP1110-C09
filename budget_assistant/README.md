# COMP1110 -- Personal Budget and Spending Assistant

Group C09 | Topic A | Tuesday 12:00 -- 12:50

---

## Overview

This is a text-based personal budget and spending assistant implemented in Python 3, enhanced with two optional graphical frontends (tkinter desktop GUI and Flask web GUI). It helps university students record daily expenses, categorize spending, set budget limits, view statistical summaries, and receive overspending alerts. All data is stored in simple JSON text files; no external dependencies are required for the core text-based mode.

The project focuses on three competencies required by the course:
1. **Problem modeling** -- real-world spending is structured into transactions, categories, and budget rules.
2. **Research and evaluation** -- existing budgeting tools were surveyed (documented in the final group report).
3. **Implementation and evidence** -- a working Python program with test cases and case studies.

---

## Execution Environment

- **Language:** Python 3.8 or higher
- **Operating system:** Cross-platform (tested on Windows, macOS, Linux)
- **Dependencies (text mode):** None (Python standard library only)
- **Dependencies (tkinter GUI):** tkinter (included with Python on most systems)
- **Dependencies (web GUI):** Flask 3.x (`pip install flask`)
- **Execution modes:** Text menu, desktop GUI, or web browser

---

## File Structure

```
budget_assistant/
|
|-- main.py                   # Entry point -- text-based interactive menu (PRIMARY)
|-- gui_tkinter.py            # Desktop graphical user interface (tkinter)
|-- gui_web.py                # Web graphical user interface (Flask)
|-- models.py                 # Data classes: Transaction, BudgetRule
|-- storage.py                # File I/O: JSON load/save for transactions and rules
|-- statistics.py             # Summary computation: totals, trends, top categories
|-- alerts.py                 # Rule-based alert engine + extra heuristics
|-- test_generator.py         # Synthetic transaction generator for testing
|-- run_case_studies.py       # Batch runner that executes all 6 case studies
|-- README.md                 # This file
|-- .gitignore                # Git ignore patterns
|
|-- case_studies/
|   |-- case1_daily_food/         # Case Study 1 -- Daily food budget HK$50
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case2_transport/          # Case Study 2 -- Monthly transport tracking
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case3_subscriptions/      # Case Study 3 -- Subscription creep detection
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case4_overspend/          # Case Study 4 -- Consecutive overspend pattern
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case5_entertainment/      # Case Study 5 -- Entertainment percentage alert
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case6_zero_spending/      # Case Study 6 -- Zero spending edge case
|   |   |-- transactions.json
|   |   |-- budget_rules.json
|   |-- case_study_outputs.txt    # Combined output of all 6 case runs
|
|-- data/                       # Runtime data folder (auto-created, git-ignored)
    |-- transactions.json
    |-- budget_rules.json
    |-- categories.txt
```

---

## How to Run

### Option 1 -- Text-Based Menu (PRIMARY -- required)

Open a terminal in the `budget_assistant` folder and run:

```bash
python3 main.py
```

The program will display a numbered menu. Choose an option by typing its number and pressing Enter.

**Menu options:**
1. **Add Transaction** -- manually enter a new expense.
2. **View / Filter Transactions** -- browse or filter by date range and category.
3. **Spending Summaries** -- view totals by category, monthly/weekly breakdowns, 7-day and 30-day trends, and top categories.
4. **Manage Budget Rules** -- add, list, or delete budget rules (daily/weekly/monthly/yearly caps and percentage thresholds).
5. **Run Alerts** -- evaluate all rules and extra heuristics (consecutive overspend, uncategorized warnings).
6. **Manage Categories** -- view or reset the default category list.
7. **Load Demo Data** -- instantly populate the system with synthetic test data.
8. **Save Data** -- manually persist current state to disk.
0. **Exit** -- save and quit.

### Option 2 -- Desktop GUI (tkinter)

```bash
python3 gui_tkinter.py
```

A multi-tab window will open with:
- **Transactions** -- view, filter, and delete transactions
- **Add Transaction** -- form-based data entry with validation
- **Summaries** -- full statistics display (totals, trends, breakdowns)
- **Budget Rules** -- add, list, and delete rules
- **Alerts** -- run alert evaluation and display results
- **Case Studies** -- load any of the 6 pre-built scenarios with one click

### Option 3 -- Web GUI (Flask)

```bash
pip install flask
python3 gui_web.py
```

Open your browser to `http://127.0.0.1:5000/` and navigate through the pages:
- **Dashboard** -- key metrics at a glance
- **Transactions** -- paginated/filtered list with delete support
- **Add** -- form-based transaction entry
- **Summaries** -- full statistics with category shares and trends
- **Rules** -- budget rule management
- **Alerts** -- alert evaluation results
- **Case Studies** -- load and preview all 6 scenarios

### Batch Case Study Mode

To run all six case studies automatically and produce a single output file:

```bash
python3 run_case_studies.py
```

Results are written to `case_studies/case_study_outputs.txt`.

---

## Data Formats

### Transaction JSON (`transactions.json`)

```json
[
  {
    "txn_id": 1,
    "date": "2025-04-01",
    "amount": 35.00,
    "category": "Food",
    "description": "Canteen lunch",
    "notes": ""
  }
]
```

### Budget Rule JSON (`budget_rules.json`)

```json
[
  {
    "rule_id": 1,
    "category": "Food",
    "period": "daily",
    "threshold": 50.0,
    "alert_type": "cap"
  }
]
```

- `period`: `daily`, `weekly`, `monthly`, or `yearly`
- `alert_type`: `cap` (absolute spending limit) or `percentage` (share of total)
- `category`: use `*` to target all categories

---

## Case Studies

Six realistic student spending scenarios are provided in the `case_studies/` folder:

1. **Daily Food Budget HK$50** -- A student tries to cap daily food spending. Alerts trigger when daily food exceeds HK$50. Demonstrates daily category caps and consecutive overspend detection.
2. **Monthly Transport Tracking** -- Tracks MTR, bus, taxi, and ferry expenses against a monthly transport budget. Shows how occasional one-off trips push the total over a monthly cap, triggering both cap and percentage alerts.
3. **Subscription Creep Detection** -- A student gradually adds Netflix, Spotify, gym, Adobe, and VPN subscriptions over four months. Illustrates how small recurring charges accumulate and breach a monthly cap.
4. **Consecutive Overspend Pattern** -- A student overspends on food for five consecutive days due to stress eating and social dining. Demonstrates the consecutive-overspend heuristic alert, which catches patterns the simple daily cap misses.
5. **Entertainment Percentage Alert** -- A student with otherwise balanced spending has entertainment costs explode (concert, karaoke, games). Shows how percentage-type rules catch disproportionate spending in a single category.
6. **Zero Spending Edge Case** -- A holiday week with only free activities and $0 transactions. Tests zero-division guards, empty-dataset handling, and ensures the system does not crash on minimal data.

---

## Error Handling

The program gracefully handles common file and input problems:

- **Missing files:** If `transactions.json` or `budget_rules.json` does not exist, the program starts with empty lists and prints an informational message.
- **Empty files:** Empty JSON files are treated as empty datasets.
- **Malformed JSON:** Invalid JSON syntax is caught, reported, and skipped; the program continues with an empty dataset.
- **Invalid transaction fields:** Corrupt records inside a JSON array are individually skipped with a warning.
- **User input validation:** Dates must follow `YYYY-MM-DD`. Amounts must be non-negative numbers. Menu choices must be valid integers. Categories cannot be empty.
- **Zero spending:** All summary and alert functions guard against division by zero.

---

## Testing

### Quick Manual Tests

1. Launch `python3 main.py`, select **7** to load demo data, then **3** to view summaries.
2. Select **5** to run alerts and verify that rule-based alerts fire correctly.
3. Add a custom transaction via option **1**, then view it via option **2**.
4. Delete a budget rule via option **4** -> **3**, then run alerts again to confirm silence.
5. Open `gui_tkinter.py` or `gui_web.py` and repeat the above through the GUI.

### Edge Cases Covered by `test_generator.py`

- `generate_zero_spending_case()` -- empty transaction list (tests division-by-zero guards).
- `generate_all_uncategorized(count)` -- every transaction in the `Others` bucket (tests uncategorized warnings).

---

## GitHub Repository

The final source code is maintained in the following public GitHub repository:
https://github.com/LiuLeshan12138/COMP1110-C09.git

---

## License

This project is created for academic purposes as part of COMP1110 coursework.
