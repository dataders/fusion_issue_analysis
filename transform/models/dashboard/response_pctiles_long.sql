select
    week,
    percentile,
    hours
from {{ ref('response_pctiles') }}
unpivot (hours for percentile in (p25, p50, p75))
order by week, percentile
