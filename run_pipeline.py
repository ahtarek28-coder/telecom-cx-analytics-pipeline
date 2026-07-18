"""
Runs the full pipeline locally, no Airflow required:
generate synthetic data -> load into DuckDB -> dbt run -> dbt test.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DBT_DIR = ROOT / "dbt"
DB_PATH = ROOT / "telecom_cx.duckdb"


def find_dbt():
    """Locate the dbt executable even when its install directory isn't on PATH.

    pip installs the dbt console-script into a directory tied to the Python
    interpreter that ran pip -- Scripts/ on Windows (a subfolder, NOT next to
    python.exe itself), bin/ on macOS/Linux (alongside python there). That
    directory is reliably known even if PATH doesn't include it.
    """
    dbt_path = shutil.which("dbt")
    if dbt_path:
        return dbt_path
    python_dir = Path(sys.executable).parent
    candidates = [
        python_dir / "Scripts" / "dbt.exe",  # Windows: Scripts/ subfolder
        python_dir / "dbt",  # macOS/Linux: bin/ alongside python
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return "dbt"


def run(cmd, cwd=None, env=None):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd, env=env)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    run([sys.executable, "data_generator/generate_data.py"], cwd=ROOT)
    run([sys.executable, "data_generator/load_to_duckdb.py"], cwd=ROOT)

    dbt_cmd = find_dbt()
    dbt_env = {**os.environ, "TELECOM_CX_DB_PATH": str(DB_PATH)}
    run(
        [dbt_cmd, "run", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        env=dbt_env,
    )
    run(
        [dbt_cmd, "test", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        env=dbt_env,
    )
    print("\nDone. Query the result, e.g.:")
    print(
        "  python -c \"import duckdb; "
        "print(duckdb.connect('telecom_cx.duckdb')"
        ".sql('select * from marts.mart_cx_kpi_rollup limit 10').df())\""
    )


if __name__ == "__main__":
    main()
