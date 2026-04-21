with opened as (
    select date_trunc('week', created_at)::date as week, count(*) as opened
    from {{ ref('fct_issues') }} where issue_category != 'epic'
    group by 1
),
closed as (
    select date_trunc('week', closed_at)::date as week, count(*) as closed
    from {{ ref('fct_issues') }} where closed_at is not null and issue_category != 'epic'
    group by 1
)
select
    strftime(coalesce(o.week, c.week), '%Y-%m-%d') as week,
    coalesce(o.opened, 0) as opened,
    coalesce(c.closed, 0) as closed
from opened o full outer join closed c on o.week = c.week
order by 1
