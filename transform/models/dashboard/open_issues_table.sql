select
    issue_number as "#",
    title,
    issue_category as type,
    round(datediff('day', created_at, current_date), 0) as age_days,
    reactions_total_count as reactions,
    comments_total_count as comments,
    coalesce(milestone_title, '') as milestone
from {{ ref('fct_issues') }}
where state = 'OPEN' and issue_category != 'epic'
order by created_at asc
limit 50
