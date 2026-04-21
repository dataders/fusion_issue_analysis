select
    strftime(date_trunc('week', closed_at), '%Y-%m-%d') as week,
    issue_category,
    round(median(hours_to_close) / 24.0, 1) as median_days,
    count(*) as n
from {{ ref('fct_issues') }}
where closed_at is not null and issue_category in ('bug', 'enhancement')
group by 1, 2
having count(*) >= 2
order by 1
