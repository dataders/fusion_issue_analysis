with weeks as (
    select
        date_trunc('week', created_at)::date as week,
        count(*) as opened
    from fct_issues where issue_category != 'epic'
    group by 1
),
closed_weeks as (
    select
        date_trunc('week', closed_at)::date as week,
        count(*) as closed
    from fct_issues where closed_at is not null and issue_category != 'epic'
    group by 1
),
combined as (
    select
        coalesce(w.week, c.week) as week,
        coalesce(w.opened, 0) as opened,
        coalesce(c.closed, 0) as closed
    from weeks w
    full outer join closed_weeks c on w.week = c.week
)
select
    strftime(week, '%Y-%m-%d') as week,
    sum(opened) over (order by week) as cumulative_opened,
    sum(closed) over (order by week) as cumulative_closed
from combined
order by week
