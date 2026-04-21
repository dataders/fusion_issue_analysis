select
    date_trunc('week', created_at) as week,
    count(*) as issues_opened
from {{ ref('fct_issues') }}
group by week
order by week
