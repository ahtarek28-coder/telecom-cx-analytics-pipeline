-- Generalized version of the telecom CEM KPI rollup pattern documented in
-- data-engineering-skills/sql-and-data-modeling/examples/multi-source-kpi-rollup-telecom-cem.md
--
-- Two deliberate improvements over the original pattern, both called out as
-- gotchas in that write-up:
--   1. complaints_technical is DISTINCT on (msisdn, sr_classification) before
--      the join, so a subscriber with multiple technical tickets in the
--      window can't inflate the other aggregates (SUM/AVG on sub/net_data/
--      net_voice columns) -- the original query didn't guarantee this.
--   2. the complaint count column is named total_technical_complaints, not
--      total_complaints -- the original name implied "all complaints" but
--      the value was already filtered to technical ones only.

with complaints_technical as (
    select distinct
        msisdn,
        sr_classification
    from {{ ref('stg_complaints') }}
    where sr_classification = 'Technical'
)

select
    coalesce(loc.h09toh16_site, loc.h17toh00_site, loc.h01toh08_site) as site_id,
    sub.screen_type,
    sub.p_segment,
    cmp.sr_classification,
    case
        when date_diff('day', sub.line_subscription_date, sub.dt) <= 30  then 'Less than 1 Month'
        when date_diff('day', sub.line_subscription_date, sub.dt) <= 60  then 'Less than 2 Months'
        when date_diff('day', sub.line_subscription_date, sub.dt) <= 90  then 'Less than 3 Months'
        when date_diff('day', sub.line_subscription_date, sub.dt) <= 180 then 'Less than 6 Months'
        else 'Greater than 6 Months'
    end as tenure_bucket,
    count(distinct sub.msisdn) as total_subs,
    count(distinct cmp.msisdn) as total_technical_complaints,
    count(distinct chn.msisdn) as total_churned_users,
    avg(sub.arpu) as avg_arpu,
    sum(sub.voice_traffic) as total_voice_traffic,
    avg(net_voice.call_success_ratio_2g) as avg_call_success_2g,
    avg(sub.volte_success_ratio) as avg_volte_success,
    avg(net_voice.call_drop_ratio_2g) as avg_call_drop_2g,
    avg(sub.volte_drop_ratio) as avg_volte_drop,
    sum(net_data.data_traffic) / 8388608.0 as total_data_gb,
    sum(net_data.dl_traffic_4g) / 8388608.0 as total_dl_4g_gb,
    sum(net_data.dl_traffic_5g) / 8388608.0 as total_dl_5g_gb,
    avg(net_data.dl_throughput_4g) as avg_dl_throughput_4g,
    avg(net_data.dl_throughput_5g) as avg_dl_throughput_5g
from {{ ref('stg_subscribers') }} sub
left join {{ ref('stg_network_data') }} net_data
    on sub.msisdn = net_data.msisdn
left join {{ ref('stg_device_location') }} loc
    on sub.msisdn = loc.msisdn
left join {{ ref('stg_network_voice') }} net_voice
    on sub.msisdn = net_voice.msisdn
left join complaints_technical cmp
    on sub.msisdn = cmp.msisdn
left join {{ ref('stg_churn') }} chn
    on sub.msisdn = chn.msisdn
group by 1, 2, 3, 4, 5
