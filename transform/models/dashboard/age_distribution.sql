select
    issue_category,
    case
        when datediff('day', created_at, current_date) <= 7 then '0-7d'
        when datediff('day', created_at, current_date) <= 30 then '8-30d'
        when datediff('day', created_at, current_date) <= 90 then '31-90d'
        when datediff('day', created_at, current_date) <= 180 then '91-180d'
        else '180d+'
    end as age_bucket,
    count(*) as issue_count
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
group by 1, 2
