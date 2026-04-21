select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    round(median(hours_to_close) / 24, 1) as median_days
from {{ ref('fct_issues') }}
where issue_category = 'enhancement' and closed_at is not null
group by date_trunc('week', closed_at)
having count(*) >= 2
order by week
