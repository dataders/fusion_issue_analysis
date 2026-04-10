select distinct
    milestone_number,
    milestone_title,
    milestone_description,
    milestone_state,
    milestone_due_on,
    milestone_created_at,
    milestone_closed_at
from {{ ref('stg_issues') }}
where milestone_number is not null
