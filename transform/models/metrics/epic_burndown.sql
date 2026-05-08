with epic_children as (
    select
        e.epic_number,
        e.title as epic_title,
        i.issue_number,
        i.created_at,
        i.closed_at
    from {{ ref('fct_epics') }} e
    join {{ ref('fct_issues') }} i
        on i.parent_number = e.epic_number
),

date_spine as (
    select
        ((select min(created_at::date) from epic_children) + (i || ' days')::interval)::date as date_day
    from generate_series(
        0::bigint,
        (select datediff('day', min(created_at::date), current_date)::bigint from epic_children)
    ) as t(i)
),

epics as (
    select distinct epic_number, epic_title from epic_children
)

select
    d.date_day,
    e.epic_number,
    e.epic_title,
    count(case when ec.created_at::date <= d.date_day then 1 end) as cumulative_opened,
    count(case when ec.closed_at::date <= d.date_day then 1 end) as cumulative_closed,
    count(case when ec.created_at::date <= d.date_day then 1 end)
        - count(case when ec.closed_at::date <= d.date_day then 1 end) as open_at_date
from date_spine d
cross join epics e
left join epic_children ec
    on ec.epic_number = e.epic_number
group by d.date_day, e.epic_number, e.epic_title
