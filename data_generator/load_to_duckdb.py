"""
Loads the CSVs from data/raw/ into a local DuckDB database (telecom_cx.duckdb)
under the `raw` schema, which the dbt project reads from via sources.yml.
"""
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "telecom_cx.duckdb"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

TABLES = [
    "subscribers",
    "device_location",
    "network_voice",
    "network_data",
    "complaints",
    "churn_label",
]


def main():
    con = duckdb.connect(str(DB_PATH))
    con.execute("create schema if not exists raw")
    for table in TABLES:
        csv_path = RAW_DIR / f"{table}.csv"
        con.execute(
            f"""
            create or replace table raw.{table} as
            select * from read_csv_auto('{csv_path.as_posix()}', header=true)
            """
        )
        row_count = con.execute(f"select count(*) from raw.{table}").fetchone()[0]
        print(f"Loaded raw.{table}: {row_count:,} rows from {csv_path.name}")
    con.close()


if __name__ == "__main__":
    main()
