# Telecom CX Analytics Pipeline

An end-to-end data pipeline: synthetic subscriber, network-performance, complaints, and churn data, transformed into a segmented CX reporting model with dbt, orchestrated with Airflow.

Built as a generalized, public-data version of real reporting patterns from telecom customer-experience analytics work — see [data-engineering-skills](https://github.com/ahtarek28-coder/data-engineering-skills) for the underlying SQL techniques this project is built on (fallback key resolution, aggregate-before-join, multi-snapshot alignment, tenure bucketing). Full design in [docs/architecture.md](docs/architecture.md).

## Status

Verified end-to-end both ways: `python run_pipeline.py` locally (7/7 dbt models built, 11/11 tests passed, 7/7 dqcheck checks passed), and as a real, scheduled Airflow DAG (`telecom_cx_analytics_pipeline`) running on a dedicated Linux server — all five tasks (`generate_synthetic_data` → `load_raw_to_duckdb` → `dbt_run` → `dbt_test` → `dq_check`) complete successfully under the actual Airflow scheduler/webserver, not just via the DAG file being present.

## Tech Stack

- **Orchestration:** Airflow (DAG provided; optional for local runs)
- **Transformation:** dbt (dbt-duckdb adapter)
- **Storage:** DuckDB — a single local file, no server needed
- **Data:** synthetic, generated to resemble telecom subscriber/network/complaint/churn tables at a realistic grain

## How to Run

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

python run_pipeline.py
```

This generates the synthetic CSVs, loads them into `telecom_cx.duckdb`, runs the dbt models, runs the dbt tests, and runs a [dqcheck](https://github.com/ahtarek28-coder/data-quality-toolkit) pass (`dq_checks.yml`) covering accepted-values and relationship checks that dbt's own `schema.yml` tests don't. Query the result:

```bash
python -c "import duckdb; print(duckdb.connect('telecom_cx.duckdb').sql('select * from marts.mart_cx_kpi_rollup limit 10').df())"
```

### Running under Airflow (optional)

Airflow and dbt-core are known to conflict on pinned transitive dependencies, so install them into **separate venvs**: this project's own `.venv` (per "How to Run" above) stays as-is, and Airflow gets its own, e.g. `~/airflow-venv`. The DAG (`dags/telecom_cx_pipeline_dag.py`) calls this project's `python`/`dbt` by absolute path (`<project>/.venv/bin/...`), not whatever's on Airflow's own PATH — override the location via the `PIPELINE_VENV_BIN` env var if your venv isn't a sibling `.venv` of this project.

```bash
python3 -m venv ~/airflow-venv
source ~/airflow-venv/bin/activate
pip install --upgrade pip

AIRFLOW_VERSION=2.10.4
PYTHON_VERSION="$(python3 --version | cut -d' ' -f2 | cut -d. -f1-2)"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

export AIRFLOW_HOME=~/airflow
airflow db migrate
airflow users create --username admin --password admin \
  --firstname Admin --lastname User --role Admin --email you@example.com

mkdir -p "$AIRFLOW_HOME/dags"
ln -s "$(pwd)/../telecom-cx-analytics-pipeline/dags/telecom_cx_pipeline_dag.py" "$AIRFLOW_HOME/dags/"

airflow webserver --port 8080 &
airflow scheduler &
```

Then trigger `telecom_cx_analytics_pipeline` from the Airflow UI (`http://<host>:8080`) or `airflow dags trigger telecom_cx_analytics_pipeline`.

## Data Model

| Table | Grain | Notes |
|---|---|---|
| `subscribers` | one row per `msisdn` | base snapshot: tenure, ARPU, voice/VoLTE KPIs |
| `device_location` | one row per `msisdn` | dimension, no date — time-of-day site columns |
| `network_voice` | one row per `msisdn` (not all covered) | latest voice network KPIs |
| `network_data` | one row per `msisdn` (not all covered) | latest data network KPIs, traffic in Kbit |
| `complaints` | many rows per `msisdn` | ticket event log |
| `churn_label` | one row per churned `msisdn` | only churned subscribers appear |

The mart, `mart_cx_kpi_rollup`, joins all of these on `msisdn` and aggregates to grain (`site_id`, `screen_type`, `p_segment`, `sr_classification`, `tenure_bucket`) — see [docs/architecture.md](docs/architecture.md) for the full breakdown and the join-cardinality reasoning.

## Roadmap

- [x] Synthetic data generator (subscriber base, network KPIs, complaints, churn labels)
- [x] dbt staging models
- [x] dbt mart model replicating the KPI rollup pattern (segmented by site/segment/tenure)
- [x] Airflow DAG scheduling the run
- [x] Data quality tests (uniqueness, not-null on join keys)
- [x] README + architecture doc
- [x] Verify the pipeline actually runs end-to-end in a real environment
- [x] Run the Airflow DAG under an actual scheduler
- [x] Add accepted-values / relationship tests beyond uniqueness and not-null (via dqcheck, not duplicated in dbt's schema.yml -- see `dq_checks.yml`)

---

### Related projects

- [dqcheck](https://github.com/ahtarek28-coder/data-quality-toolkit) — a standalone data quality checking library/CLI; verified against this project's own DuckDB database (all checks pass).

### Other planned portfolio projects (not yet scaffolded)

- **Streaming KPI demo** — Kafka + Spark, real-time network KPI aggregation instead of batch.
