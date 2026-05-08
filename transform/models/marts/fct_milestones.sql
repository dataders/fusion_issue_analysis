with milestones as (
    select * from {{ ref('dim_milestones') }}
),

issue_rollup as (
    select
        milestone_number,
        count(*)                                  as total_issues,
        count(*) filter (where state = 'OPEN')    as total_open,
        count(*) filter (where state = 'CLOSED')  as total_closed,
        count(*) filter (where is_epic)           as epic_count,
        count(*) filter (where has_epic_parent)   as task_count
    from {{ ref('fct_issues') }}
    where milestone_number is not null
    group by milestone_number
)

select
    m.milestone_number,
    m.milestone_title,
    m.milestone_state,
    m.milestone_due_on,
    m.milestone_created_at,
    m.milestone_closed_at,

    coalesce(r.total_issues,  0) as total_issues,
    coalesce(r.total_open,    0) as total_open,
    coalesce(r.total_closed,  0) as total_closed,
    coalesce(r.epic_count,    0) as epic_count,
    coalesce(r.task_count,    0) as task_count,

    case
        when coalesce(r.total_issues, 0) = 0 then null
        else r.total_closed::float / r.total_issues
    end                          as pct_complete,

    case
        when m.milestone_state = 'OPEN'
            and m.milestone_due_on is not null
            and m.milestone_due_on::date < current_date
        then true else false
    end                          as is_overdue
from milestones m
left join issue_rollup r
    on m.milestone_number = r.milestone_number
