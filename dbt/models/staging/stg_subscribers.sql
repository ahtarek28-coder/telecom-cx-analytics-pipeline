select
    msisdn,
    dt,
    line_type,
    line_subscription_date,
    screen_type,
    p_segment,
    arpu,
    voice_traffic,
    volte_success_ratio,
    volte_drop_ratio
from {{ source('raw', 'subscribers') }}
