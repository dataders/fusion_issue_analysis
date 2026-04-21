select
    issue_category,
    state,
    count(*) as n
from {{ ref('fct_issues') }}
group by issue_category, state
