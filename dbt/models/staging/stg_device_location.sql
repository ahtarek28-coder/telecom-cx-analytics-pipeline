select
    msisdn,
    h09toh16_site,
    h17toh00_site,
    h01toh08_site
from {{ source('raw', 'device_location') }}
