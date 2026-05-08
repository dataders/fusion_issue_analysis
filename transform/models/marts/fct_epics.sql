with epics as (
    select * from {{ ref('fct_issues') }}
    where is_epic
),

child_rollup as (
    select
        parent_number as epic_number,
        count(*)                                    as child_total,
        count(*) filter (where state = 'OPEN')      as child_open,
        count(*) filter (where state = 'CLOSED')    as child_closed
    from {{ ref('fct_issues') }}
    where parent_number is not null
    group by parent_number
)

select
    e.issue_number          as epic_number,
    e.issue_url             as epic_url,
    e.title,
    e.state,
    e.created_at,
    e.closed_at,
    e.milestone_number,
    e.milestone_title,
    e.milestone_state,
    e.milestone_due_on,

    coalesce(c.child_total,  0) as child_total,
    coalesce(c.child_open,   0) as child_open,
    coalesce(c.child_closed, 0) as child_closed,
    case
        when coalesce(c.child_total, 0) = 0 then null
        else c.child_closed::float / c.child_total
    end                         as pct_complete,

    e.milestone_number is not null      as has_milestone,
    case
        when e.state = 'OPEN' and e.milestone_number is null
        then true else false
    end                                 as is_orphan_epic
from epics e
left join child_rollup c
    on e.issue_number = c.epic_number
