"""
Airflow DAG orchestrating the telecom CX analytics pipeline:
generate synthetic data -> load into DuckDB -> dbt run -> dbt test.

Each source is generated/loaded as of its own reference date rather than a
single shared "today" -- the multi-snapshot-alignment pattern documented in
data-engineering-skills. Requires apache-airflow (see ../requirements-airflow.txt)
and the project's own requirements to be installed in the Airflow environment.
"""
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt"

with DAG(
    dag_id="telecom_cx_analytics_pipeline",
    description="Generate synthetic telecom CX data and build the KPI rollup mart",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["telecom", "cx-analytics", "demo"],
) as dag:

    generate_data = BashOperator(
        task_id="generate_synthetic_data",
        bash_command=f"python {PROJECT_ROOT / 'data_generator' / 'generate_data.py'}",
    )

    load_to_duckdb = BashOperator(
        task_id="load_raw_to_duckdb",
        bash_command=f"python {PROJECT_ROOT / 'data_generator' / 'load_to_duckdb.py'}",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )

    generate_data >> load_to_duckdb >> dbt_run >> dbt_test
