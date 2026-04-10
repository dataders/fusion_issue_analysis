-- Bug fix velocity: weekly trend of time-to-close for bug-labeled issues
with bug_issues as (
    select
        f.issue_number,
        f.created_at,
        f.closed_at,
        f.hours_to_close
    from {{ ref('fct_issues') }} f
    inner join {{ ref('fct_issue_labels') }} l
        on f.issue_dlt_id = l.issue_dlt_id
    where l.label_name = 'bug'
      and f.closed_at is not null
),

weekly as (
    select
        date_trunc('week', closed_at) as week_closed,
        count(*) as bugs_closed,
        round(avg(hours_to_close), 1) as avg_hours_to_close,
        round(median(hours_to_close), 1) as median_hours_to_close,
        round(quantile_cont(hours_to_close, 0.9), 1) as p90_hours_to_close
    from bug_issues
    group by date_trunc('week', closed_at)
)

select * from weekly
order by week_closed
