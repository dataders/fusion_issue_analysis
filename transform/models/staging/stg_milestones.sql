select
    number      as milestone_number,
    title       as milestone_title,
    description as milestone_description,
    state       as milestone_state,
    due_on      as milestone_due_on,
    created_at  as milestone_created_at,
    updated_at  as milestone_updated_at,
    closed_at   as milestone_closed_at
from {{ raw_source('milestones') }}
