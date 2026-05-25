select
    issue_number,
    title,
    state,
    created_at,
    closed_at,
    coalesce(milestone_title, '') as milestone_title,
    reactions_total_count,
    comments_total_count,
    round(datediff('day', created_at, current_date), 0) as days_open
from {{ ref('fct_issues') }}
where issue_category = 'epic'
order by state desc, days_open desc
