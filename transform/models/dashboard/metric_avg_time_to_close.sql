-- MetricFlow metric: avg_time_to_close, sliced by metric_time (week) and issue_category
select
    date_trunc('week', closed_at)::date as metric_time,
    issue_category,
    count(*) as issue_count,
    round(avg(hours_to_close), 1) as avg_hours_to_close,
    round(median(hours_to_close), 1) as median_hours_to_close,
    round(avg(hours_to_close) / 24.0, 2) as avg_days_to_close,
    round(median(hours_to_close) / 24.0, 2) as median_days_to_close
from {{ ref('fct_issues') }}
where closed_at is not null
  and issue_category in ('bug', 'enhancement', 'task', 'other')
group by 1, 2
order by 1, 2
