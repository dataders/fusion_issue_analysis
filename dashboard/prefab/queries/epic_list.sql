select
    f.issue_number,
    f.title,
    f.state,
    f.created_at,
    f.closed_at,
    f.reactions_total_count,
    f.comments_total_count
from fct_issues f
where f.issue_category = 'epic'
order by f.state desc, f.issue_number
