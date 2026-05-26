select
    milestone_number,
    milestone_title,
    milestone_description,
    milestone_state,
    milestone_due_on,
    milestone_created_at,
    milestone_closed_at
from {{ ref('stg_milestones') }}
