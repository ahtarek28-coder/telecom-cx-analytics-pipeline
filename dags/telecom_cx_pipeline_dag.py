"""
Airflow DAG orchestrating the telecom CX analytics pipeline:
generate synthetic data -> load into DuckDB -> dbt run -> dbt test.

Each source is generated/loaded as of its own reference date rather than a
single shared "today" -- the multi-snapshot-alignment pattern documented in
data-engineering-skills. Requires apache-airflow (see ../requirements-airflow.txt)
and the project's own requirements to be installed in the Airflow environment.
"""
import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = PROJECT_ROOT / "dbt"
DB_PATH = PROJECT_ROOT / "telecom_cx.duckdb"

# Airflow and dbt-core are known to conflict on pinned transitive
# dependencies (packaging, click, SQLAlchemy, ...), so the pipeline's own
# deps (pandas, duckdb, dbt-duckdb) are expected to live in a SEPARATE venv
# from Airflow's own -- not the venv Airflow itself is running in. Point
# this at that venv's bin/ directory; override via PIPELINE_VENV_BIN if
# it isn't a sibling ".venv" of this project (e.g. a differently-named or
# differently-located venv).
PIPELINE_VENV_BIN = Path(os.environ.get("PIPELINE_VENV_BIN", PROJECT_ROOT / ".venv" / "bin"))
PYTHON_BIN = PIPELINE_VENV_BIN / "python"
DBT_BIN = PIPELINE_VENV_BIN / "dbt"

# Airflow runs BashOperator tasks from their own temp working directory, so
# the duckdb path in dbt/profiles.yml can't rely on a relative path -- pass
# it explicitly instead (see the "{{ env_var(...) }}" in profiles.yml).
DBT_ENV = {**os.environ, "TELECOM_CX_DB_PATH": str(DB_PATH)}

DQ_CHECKS_CONFIG = PROJECT_ROOT / "dq_checks.yml"

# Every task's combined stdout/stderr is duplicated into one running log
# file for the whole project (in addition to Airflow's own per-task logs)
# via `tee -a`. `pipefail` is required here -- without it, a failing `cmd`
# piped into `tee` (which itself succeeds) would report exit code 0 and
# Airflow would never notice the task actually failed.
LOG_FILE = PROJECT_ROOT / "logs" / "dag_runs.log"


def with_logging(cmd: str, label: str) -> str:
    return (
        f'mkdir -p "{LOG_FILE.parent}" && '
        f'echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) [{label}] ===" >> "{LOG_FILE}" && '
        f'set -o pipefail && ({cmd}) 2>&1 | tee -a "{LOG_FILE}"'
    )


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
        bash_command=with_logging(
            f"{PYTHON_BIN} {PROJECT_ROOT / 'data_generator' / 'generate_data.py'}",
            "generate_synthetic_data",
        ),
    )

    load_to_duckdb = BashOperator(
        task_id="load_raw_to_duckdb",
        bash_command=with_logging(
            f"{PYTHON_BIN} {PROJECT_ROOT / 'data_generator' / 'load_to_duckdb.py'}",
            "load_raw_to_duckdb",
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=with_logging(
            f"{DBT_BIN} run --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}", "dbt_run"
        ),
        env=DBT_ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=with_logging(
            f"{DBT_BIN} test --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}", "dbt_test"
        ),
        env=DBT_ENV,
    )

    dq_check = BashOperator(
        task_id="dq_check",
        # dq_checks.yml's connection string is a relative path
        # ("duckdb:///telecom_cx.duckdb"), which resolves against cwd --
        # pin it to PROJECT_ROOT rather than relying on Airflow's default
        # task working directory (the same class of bug fixed for dbt above).
        bash_command=with_logging(
            f"{PYTHON_BIN} -m dqcheck.cli run --config {DQ_CHECKS_CONFIG}", "dq_check"
        ),
        cwd=str(PROJECT_ROOT),
    )

    generate_data >> load_to_duckdb >> dbt_run >> dbt_test >> dq_check
