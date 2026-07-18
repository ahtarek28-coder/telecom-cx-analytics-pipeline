# Architecture

<!--
Fill in once the pipeline is built. Suggested shape:

1. data_generator/ — produces synthetic CSV/Parquet resembling subscriber base,
   network KPIs, complaints, and churn labels at a believable grain (one row per
   msisdn per snapshot date, matching the multi-source snapshot pattern documented
   in data-engineering-skills).
2. Raw data lands in local storage (or a cheap cloud bucket for a "real" cloud demo).
3. dbt staging models clean/type each source.
4. dbt mart model reproduces the KPI rollup: segmented by site, screen type,
   customer segment, complaint classification, tenure bucket.
5. Airflow DAG schedules generation + dbt run + tests.
6. Data quality tests catch the join-fan-out and grain issues called out in the
   SQL notes (e.g. a dimension join must stay 1:1 with the base table).

Add a diagram (even a simple ASCII or draw.io export) once the shape is final.
-->
