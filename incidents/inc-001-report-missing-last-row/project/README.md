# Reporting Service

Turns a ledger export (CSV) into daily, weekly and monthly summaries for Finance.

    python -m report data/sales_2026-08.csv
    pytest -q

Ledger rows are `date,order_id,amount`. Amounts are decimal strings.
