{#
  Q: Are we closing issues as fast as they arrive?
  Issues opened vs closed per complete week, last 26 weeks. net_change > 0
  means the backlog grew that week.
#}

with a as (select as_of_date from {{ ref('as_of') }}),

weeks as (
    select (date_trunc('week', a.as_of_date) - to_days((t.i * 7)::integer))::timestamp as week
    from a cross join generate_series(0::bigint, 26::bigint) as t(i)
),

issues as (
    select created_at, closed_at
    from {{ ref('fct_issues') }}
    where issue_category != 'epic'
)

select
    strftime(w.week, '%Y-%m-%d') as week,
    count(*) filter (where i.created_at >= w.week and i.created_at < w.week + interval 7 day) as opened,
    count(*) filter (where i.closed_at >= w.week and i.closed_at < w.week + interval 7 day) as closed,
    count(*) filter (where i.created_at >= w.week and i.created_at < w.week + interval 7 day)
        - count(*) filter (where i.closed_at >= w.week and i.closed_at < w.week + interval 7 day) as net_change
from weeks w
cross join a
left join issues i
    on (i.created_at >= w.week and i.created_at < w.week + interval 7 day)
    or (i.closed_at >= w.week and i.closed_at < w.week + interval 7 day)
where w.week + interval 7 day <= a.as_of_date::timestamp  -- complete weeks only
group by 1
order by 1
