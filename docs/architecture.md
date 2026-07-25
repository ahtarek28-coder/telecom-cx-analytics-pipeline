# Architecture

```
data_generator/generate_data.py
        |  writes CSVs (subscribers, device_location, network_voice,
        |  network_data, complaints, churn_label) to data/raw/
        v
data_generator/load_to_duckdb.py
        |  loads each CSV into telecom_cx.duckdb, schema `raw`
        v
dbt (models/staging/*.sql)
        |  one staging view per source, renamed/typed, 1:1 with the source
        v
dbt (models/marts/mart_cx_kpi_rollup.sql)
        |  joins all staging models on msisdn, aggregates into the
        |  segmented KPI rollup (materialized as a table, schema `marts`)
        v
dbt test
        |  uniqueness/not-null checks on every staging model's join key
        v
dqcheck (dq_checks.yml)
        |  accepted-values + relationship checks, from a separate project
        |  (github.com/ahtarek28-coder/data-quality-toolkit) rather than
        |  duplicated in dbt's own schema.yml
```

Orchestration: `run_pipeline.py` runs all five steps locally with no scheduler. `dags/telecom_cx_pipeline_dag.py` wraps the same five steps as an Airflow DAG for scheduled runs.

## Multi-snapshot alignment

Each source is generated as of its own reference date, not a single shared "today" — mirroring the real reporting pattern documented in [data-engineering-skills](https://github.com/ahtarek28-coder/data-engineering-skills):

| Source | Reference date | Why |
|---|---|---|
| `subscribers` | `BASE_SNAPSHOT_DATE` (60 days before `END_DATE`) | subscriber base snapshot |
| `network_voice` / `network_data` | `NETWORK_SNAPSHOT_DATE` (`END_DATE`) | latest usage snapshot |
| `complaints` | rolling 30-day window ending at `END_DATE` | event log, not a snapshot |
| `churn_label` | `CHURN_SNAPSHOT_DATE` (30 days before `END_DATE`) | churn labeled as of a point in time |

These constants live at the top of `data_generator/generate_data.py`.

## Join cardinality

- `subscribers`, `device_location`, `network_voice`, `network_data`, `churn_label` are all tested `unique` + `not_null` on `msisdn` in staging — so every `LEFT JOIN` in the mart onto them is guaranteed 1:1 and can't fan out.
- `complaints` is an event log (a subscriber can have multiple tickets) and is deliberately **not** tested for uniqueness. The mart aggregates it (`distinct` on `msisdn, sr_classification`, filtered to `Technical`) in a CTE before joining, so the join itself stays 1:1 — the "aggregate-before-join" pattern.

## Data quality tests

`dbt test` runs `unique` + `not_null` on the join key of every staging model except `stg_complaints` (see above), plus a `not_null` check on `total_subs` in the mart.

Accepted-values and relationship checks (e.g. `screen_type`/`p_segment` staying within their known categories, `churn_label`/`complaints` not referencing a `msisdn` that doesn't exist in `subscribers`) are handled by [dqcheck](https://github.com/ahtarek28-coder/data-quality-toolkit) instead of dbt's own `schema.yml` -- see `dq_checks.yml` at the project root. This is a deliberate choice to reuse a separate portfolio project rather than duplicate the same logic in two places; dqcheck's `relationships` check is exactly the orphan-foreign-key check, and its `accepted_values` check is exactly the categorical-value check.
