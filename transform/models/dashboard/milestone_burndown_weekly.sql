select
    strftime(date_day, '%Y-%m-%d') as date_day,
    milestone_title,
    open_at_date
from {{ ref('milestone_burndown') }}
where date_day::date = date_trunc('week', date_day::date)
  and milestone_title in (
      select distinct milestone_title
      from {{ ref('dim_milestones') }}
      where milestone_state = 'OPEN'
  )
order by milestone_title, date_day
