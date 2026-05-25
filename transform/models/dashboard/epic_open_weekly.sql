-- Weekly count of open EPICs — used for EPIC burndown trend chart
with epics as (
    select
        created_at::date as created_date,
        closed_at::date as closed_date
    from {{ ref('fct_issues') }}
    where issue_category = 'epic'
),

date_spine as (
    select
        ((select min(created_date) from epics) + (i || ' days')::interval)::date as date_day
    from generate_series(
        0::bigint,
        (select datediff('day', min(created_date), current_date)::bigint from epics)
    ) as t(i)
),

daily as (
    select
        d.date_day,
        count(case when e.created_date <= d.date_day then 1 end)
            - count(case when e.closed_date <= d.date_day then 1 end) as open_epics
    from date_spine d
    cross join epics e
    group by d.date_day
)

select
    strftime(date_day, '%Y-%m-%d') as week,
    open_epics
from daily
where date_day = date_trunc('week', date_day)
order by date_day
