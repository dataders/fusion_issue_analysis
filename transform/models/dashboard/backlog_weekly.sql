{#
  Q: Is the backlog growing or shrinking?
  Open non-epic issues at the end of each week (the current, partial week is
  measured at as_of_date), by type. Long format: one row per (week, type).
#}

with a as (select as_of_date from {{ ref('as_of') }}),

weeks as (
    select (date_trunc('week', a.as_of_date) - to_days((t.i * 7)::integer))::date as week
    from a cross join generate_series(0::bigint, 51::bigint) as t(i)
),

issues as (
    select issue_category, created_at, closed_at
    from {{ ref('fct_issues') }}
    where issue_category != 'epic'
),

categories as (
    select * from (values ('bug'), ('feature'), ('task'), ('other')) as c(issue_category)
)

select
    strftime(w.week, '%Y-%m-%d') as week,
    c.issue_category,
    count(i.created_at) as open_issues
from weeks w
cross join categories c
left join issues i
    on i.issue_category = c.issue_category
   and i.created_at < w.week + interval 7 day
   and (i.closed_at is null or i.closed_at >= w.week + interval 7 day)
group by 1, 2
order by 1, 2
