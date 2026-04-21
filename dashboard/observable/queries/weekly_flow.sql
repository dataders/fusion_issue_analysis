with weeks as (
    select date_trunc('week', created_at)::date as week,
           count(*) as opened
    from fct_issues where issue_category != 'epic'
    group by 1
),
closed_w as (
    select date_trunc('week', closed_at)::date as week, count(*) as closed
    from fct_issues where closed_at is not null and issue_category != 'epic'
    group by 1
)
select strftime(coalesce(w.week, c.week), '%Y-%m-%d') as week,
       coalesce(w.opened,0) as opened, coalesce(c.closed,0) as closed
from weeks w full outer join closed_w c on w.week=c.week
order by 1
