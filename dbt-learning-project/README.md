# dbt Learning Shop: runnable hands-on POC

A deterministic, small e-commerce analytics project for learning dbt with Snowflake. It uses CSV seeds so you can run the full project without connecting to a production source system. No AI APIs are used.

## Prerequisites

- Python 3.9+ recommended
- A Snowflake account and a role, warehouse, database, and schema you can use
- A dbt adapter compatible with your chosen dbt Core version

## 1. Install dbt

Create and activate a virtual environment, then install the Snowflake adapter:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install dbt-snowflake
dbt --version
```

## 2. Configure credentials safely

Copy `profiles.yml.example` to `~/.dbt/profiles.yml`. Replace the placeholders with your Snowflake settings. Prefer SSO/key-pair authentication for real environments; never commit credentials. Confirm the profile file is outside this repository.

## 3. Run the project

From this directory:

```bash
dbt debug --profiles-dir ~/.dbt
dbt seed --profiles-dir ~/.dbt
dbt compile --profiles-dir ~/.dbt
dbt run --profiles-dir ~/.dbt
dbt test --profiles-dir ~/.dbt
dbt build --profiles-dir ~/.dbt
```

If you prefer one command after configuration, `dbt build` runs seeds/models/tests in dependency order. Review your dbt Core version if a YAML test syntax differs; this example uses the modern `data_tests` key and `arguments` syntax.

## Project flow

```text
customers.csv -> customers seed -> stg_customers -> dim_customers
orders.csv    -> orders seed    -> stg_orders    -> fct_orders
payments.csv  -> payments seed  -> stg_payments  -> fct_orders
```

- **Seeds**: small, version-controlled CSV reference/demo data.
- **Staging models**: cast types, normalize text, and give source columns consistent names.
- **Marts**: business-friendly customer dimension and orders fact.
- **Tests**: unique, not-null, and relationships checks.
- **Lineage**: `ref()` tells dbt about dependencies and build order.

## Exercises

1. Change `stg_customers` to trim/lowercase email and run `dbt build --select stg_customers+`.
2. Add an accepted-values test for order status (completed, returned, cancelled).
3. Add a `net_revenue` metric to `fct_orders` that excludes returned/cancelled orders. State your business definition first.
4. Add a macro to normalize emails, then use it in `stg_customers`.
5. Add an incremental model only after explaining its grain, unique key, and late-arriving-data strategy.
6. Create a snapshot for customer country changes; use a disposable schema because snapshots create historical records.
7. Inspect compiled SQL and Snowflake Query Profile before optimizing.
8. Add CI that runs `dbt deps`, `dbt parse`, `dbt compile`, and selected tests with secrets stored in GitHub Actions, never in YAML.

## Expected output sanity checks

With the supplied seeds:
- 5 customer rows in `stg_customers`
- 6 order rows in `fct_orders`
- 4 completed orders
- Order 1004 has payment amount 220.00
- Customer 1 has 2 orders

Run `select * from <your_database>.DBT_LEARNING.FCT_ORDERS order by order_id;` using the actual database/schema configured in your profile. dbt's final schema name follows your profile and project configuration.

## Troubleshooting checklist

- `dbt debug`: adapter/profile/connectivity errors.
- `dbt parse`: project/YAML/Jinja syntax errors.
- `dbt compile`: inspect generated SQL and refs.
- `dbt test`: inspect failing rows before changing tests.
- `dbt ls --select +fct_orders`: inspect selected upstream lineage.
- Never use `--full-refresh` or snapshots against a shared production schema while experimenting.
