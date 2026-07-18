-- Event log: intentionally NOT deduplicated by msisdn here -- a customer can
-- file multiple tickets in the window. Aggregation/dedup happens downstream,
-- in the mart, right before the join (see complaints_technical CTE in
-- mart_cx_kpi_rollup.sql) -- this is the "aggregate-before-join" pattern
-- documented in data-engineering-skills.
select
    msisdn,
    dt,
    sr_classification
from {{ source('raw', 'complaints') }}
