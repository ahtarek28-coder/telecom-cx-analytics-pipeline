# Telecom CX Analytics Pipeline

An end-to-end data pipeline: synthetic subscriber, network-performance, complaints, and churn data, transformed into a segmented CX reporting model with dbt, orchestrated with Airflow.

Built as a generalized, public-data version of real reporting patterns from telecom customer-experience analytics work — see [data-engineering-skills](https://github.com/ahtarek28-coder/data-engineering-skills) for the underlying SQL techniques this project is built on (fallback key resolution, aggregate-before-join, multi-snapshot alignment, tenure bucketing). Full design in [docs/architecture.md](docs/architecture.md).

## Status

Verified end-to-end locally: `python run_pipeline.py` generates the synthetic data, loads it into DuckDB, and runs `dbt run` (7/7 models built) and `dbt test` (11/11 tests passed). The Airflow DAG uses the same steps but hasn't been run under an actual Airflow scheduler yet.

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

This generates the synthetic CSVs, loads them into `telecom_cx.duckdb`, runs the dbt models, and runs the dbt tests. Query the result:

```bash
python -c "import duckdb; print(duckdb.connect('telecom_cx.duckdb').sql('select * from marts.mart_cx_kpi_rollup limit 10').df())"
```

### Running under Airflow (optional)

```bash
pip install -r requirements-airflow.txt
```

Point your `AIRFLOW_HOME`'s `dags/` folder at (or symlink) `dags/telecom_cx_pipeline_dag.py`, then trigger `telecom_cx_analytics_pipeline` from the Airflow UI/CLI.

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
- [ ] Run the Airflow DAG under an actual scheduler (only run via `run_pipeline.py` so far)
- [ ] Add accepted-values / relationship tests beyond uniqueness and not-null

---

### Other planned portfolio projects (not yet scaffolded)

- **Streaming KPI demo** — Kafka + Spark, real-time network KPI aggregation instead of batch.
- **Data quality framework** — a small reusable library/CLI for the kind of join-fan-out and grain checks documented in `data-engineering-skills`.
