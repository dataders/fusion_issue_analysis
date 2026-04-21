select
    strftime(date_trunc('week', created_at), '%Y-%m-%d') as week,
    round(quantile_cont(hours_to_first_response, 0.25), 1) as p25,
    round(quantile_cont(hours_to_first_response, 0.50), 1) as p50,
    round(quantile_cont(hours_to_first_response, 0.75), 1) as p75
from {{ ref('fct_issues') }}
where hours_to_first_response is not null and issue_category != 'epic'
group by date_trunc('week', created_at)
having count(*) >= 3
order by week
