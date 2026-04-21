with weeks as (
    select
        date_trunc('week', created_at)::date as week,
        count(*) as opened,
        count(case when issue_category = 'bug' then 1 end) as bugs_opened,
        count(case when issue_category = 'enhancement' then 1 end) as enhancements_opened
    from fct_issues where issue_category != 'epic'
    group by 1
),
closed_weeks as (
    select
        date_trunc('week', closed_at)::date as week,
        count(*) as closed,
        count(case when issue_category = 'bug' then 1 end) as bugs_closed,
        count(case when issue_category = 'enhancement' then 1 end) as enhancements_closed
    from fct_issues where closed_at is not null and issue_category != 'epic'
    group by 1
),
combined as (
    select
        coalesce(w.week, c.week) as week,
        coalesce(w.opened, 0) as opened,
        coalesce(c.closed, 0) as closed,
        coalesce(w.bugs_opened, 0) as bugs_opened,
        coalesce(c.bugs_closed, 0) as bugs_closed,
        coalesce(w.enhancements_opened, 0) as enh_opened,
        coalesce(c.enhancements_closed, 0) as enh_closed
    from weeks w
    full outer join closed_weeks c on w.week = c.week
)
select
    strftime(week, '%Y-%m-%d') as week,
    sum(opened) over (order by week) as cumulative_opened,
    sum(closed) over (order by week) as cumulative_closed,
    sum(bugs_opened) over (order by week) as cum_bugs_opened,
    sum(bugs_closed) over (order by week) as cum_bugs_closed,
    sum(enh_opened) over (order by week) as cum_enh_opened,
    sum(enh_closed) over (order by week) as cum_enh_closed
from combined
order by week
