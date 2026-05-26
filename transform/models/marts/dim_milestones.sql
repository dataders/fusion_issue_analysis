-- SELECT DISTINCT on all columns doesn't deduplicate by milestone_number:
-- a milestone whose state/due_date changes across issues yields multiple rows.
-- Use a window function to keep one row per milestone (most recent state wins).
with milestones as (
    select
        milestone_number,
        milestone_title,
        milestone_description,
        milestone_state,
        milestone_due_on,
        milestone_created_at,
        milestone_closed_at,
        row_number() over (
            partition by milestone_number
            order by
                case when milestone_state = 'CLOSED' then 0 else 1 end,
                milestone_closed_at desc nulls last,
                milestone_due_on    desc nulls last
        ) as rn
    from {{ ref('stg_issues') }}
    where milestone_number is not null
)

select
    milestone_number,
    milestone_title,
    milestone_description,
    milestone_state,
    milestone_due_on,
    milestone_created_at,
    milestone_closed_at
from milestones
where rn = 1
