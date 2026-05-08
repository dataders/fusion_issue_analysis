select
    issue_number,
    issue_url,
    title,
    issue_type,
    state,
    created_at,
    (current_date - created_at::date) as age_days
from {{ ref('fct_issues') }}
where is_orphan
order by created_at
