select
    msisdn,
    dt,
    call_success_ratio_2g,
    call_drop_ratio_2g
from {{ source('raw', 'network_voice') }}
