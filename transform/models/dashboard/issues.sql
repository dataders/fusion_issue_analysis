select
    issue_number,
    title,
    state,
    issue_category,
    created_at,
    closed_at,
    hours_to_close,
    hours_to_first_response,
    reactions_total_count,
    comments_total_count,
    milestone_title,
    is_labeled,
    is_assigned,
    has_milestone,
    author_login
from {{ ref('fct_issues') }}
order by issue_number desc
