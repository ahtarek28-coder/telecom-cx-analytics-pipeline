# Telecom CX Analytics Pipeline

An end-to-end data pipeline demo: ingesting synthetic subscriber, network-performance, complaints, and churn data, transforming it into a segmented reporting model, and orchestrating the whole thing on a schedule.

Built as a generalized, public-data version of real reporting patterns from telecom customer-experience analytics work — see [data-engineering-skills](https://github.com/ahtarek28-coder/data-engineering-skills) for the underlying SQL techniques this project is built on (fallback key resolution, aggregate-before-join, multi-snapshot alignment, tenure bucketing).

## Status

🚧 Scaffolding stage — architecture and structure defined, implementation in progress.

## Problem

<!-- One paragraph: what business question does this pipeline answer, and why does it need more than a single query? -->

## Architecture

<!-- Diagram + description once built. Rough shape:
  synthetic data generator -> raw storage -> dbt staging/marts -> Airflow schedule -> reporting table -->

## Tech Stack

- **Orchestration:** Airflow
- **Transformation:** dbt
- **Storage:** <!-- e.g. DuckDB/Postgres for a local-runnable demo -->
- **Data:** synthetic, generated to resemble telecom subscriber/network/complaint/churn tables at a realistic grain

## How to Run

<!-- Fill in once the pipeline is runnable end-to-end. -->

## Data Model

<!-- Fact/dim structure, grain of each table, keys. -->

## Roadmap

- [ ] Synthetic data generator (subscriber base, network KPIs, complaints, churn labels)
- [ ] dbt staging models
- [ ] dbt mart model replicating the KPI rollup pattern (segmented by site/segment/tenure)
- [ ] Airflow DAG scheduling the daily/monthly run
- [ ] Data quality tests (uniqueness, not-null, referential integrity on the join keys)
- [ ] README: architecture diagram + how-to-run

---

### Other planned portfolio projects (not yet scaffolded)

- **Streaming KPI demo** — Kafka + Spark, real-time network KPI aggregation instead of batch.
- **Data quality framework** — a small reusable library/CLI for the kind of join-fan-out and grain checks documented in `data-engineering-skills` (e.g. "does this join preserve cardinality," "does this snapshot column have exactly one row per key").
