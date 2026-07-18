-- Only churned msisdns appear in the source table (a label table, not a
-- full population with a boolean flag) -- counting distinct msisdn after
-- the join gives the churned-user count directly.
select
    msisdn,
    dt
from {{ source('raw', 'churn_label') }}
