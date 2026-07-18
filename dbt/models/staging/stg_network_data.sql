select
    msisdn,
    dt,
    data_traffic,
    dl_traffic_4g,
    dl_traffic_5g,
    dl_throughput_4g,
    dl_throughput_5g
from {{ source('raw', 'network_data') }}
