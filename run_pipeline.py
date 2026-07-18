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


def find_dbt():
    """Locate the dbt executable even when its install directory isn't on PATH.

    pip installs the dbt console-script next to the Python interpreter that
    ran pip (Scripts/ on Windows, bin/ on macOS/Linux) -- that directory is
    reliably known even if PATH doesn't include it.
    """
    dbt_path = shutil.which("dbt")
    if dbt_path:
        return dbt_path
    candidate = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    return str(candidate) if candidate.exists() else "dbt"


def run(cmd, cwd=None):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main():
    run([sys.executable, "data_generator/generate_data.py"], cwd=ROOT)
    run([sys.executable, "data_generator/load_to_duckdb.py"], cwd=ROOT)
    dbt_cmd = find_dbt()
    run([dbt_cmd, "run", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)])
    run([dbt_cmd, "test", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)])
    print("\nDone. Query the result, e.g.:")
    print(
        "  python -c \"import duckdb; "
        "print(duckdb.connect('telecom_cx.duckdb')"
        ".sql('select * from marts.mart_cx_kpi_rollup limit 10').df())\""
    )


if __name__ == "__main__":
    main()
