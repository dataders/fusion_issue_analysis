select
    issue_number,
    title,
    state,
    created_at,
    closed_at,
    reactions_total_count,
    comments_total_count
from {{ ref('fct_issues') }}
where issue_category = 'epic'
order by state desc, issue_number
