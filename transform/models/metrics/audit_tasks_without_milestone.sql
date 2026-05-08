select
    issue_number,
    issue_url,
    title,
    issue_type,
    parent_number,
    parent_title,
    state,
    created_at
from {{ ref('fct_issues') }}
where state = 'OPEN'
  and has_epic_parent
  and milestone_number is null
order by created_at
