{#
  Q: Where do things stand right now?
  One row. All windows are the 28 days ending at as_of_date (see as_of).
  Response SLA only counts issues opened at least 48h before as_of_date, and
  an issue with no response counts as a miss — so recent weeks aren't
  flattered by leaving out the issues nobody has answered yet.
#}

with a as (select as_of_date from {{ ref('as_of') }}),

i as (
    select f.*, a.as_of_date
    from {{ ref('fct_issues') }} f cross join a
    where f.issue_category != 'epic'
)

select
    count(*) filter (where state = 'OPEN') as open_issues,
    count(*) filter (
        where created_at < as_of_date - interval 28 day
          and (closed_at is null or closed_at >= as_of_date - interval 28 day)
    ) as open_issues_28d_ago,
    count(*) filter (where created_at >= as_of_date - interval 28 day) as opened_28d,
    count(*) filter (where closed_at >= as_of_date - interval 28 day) as closed_28d,
    count(*) filter (where created_at >= as_of_date - interval 28 day)
        - count(*) filter (where closed_at >= as_of_date - interval 28 day) as backlog_change_28d,

    count(*) filter (where state = 'OPEN' and triage_status = 'awaiting_triage') as awaiting_triage,
    round(median(date_diff('day', created_at, as_of_date))
        filter (where state = 'OPEN' and triage_status = 'awaiting_triage'), 0) as awaiting_triage_median_age_days,

    round(100.0 * count(*) filter (
            where created_at >= as_of_date - interval 30 day
              and created_at < as_of_date - interval 2 day
              and hours_to_first_response <= 48)
        / nullif(count(*) filter (
            where created_at >= as_of_date - interval 30 day
              and created_at < as_of_date - interval 2 day), 0), 0) as pct_responded_48h_28d,
    round(median(hours_to_first_response) filter (
        where created_at >= as_of_date - interval 28 day), 1) as median_hours_to_first_response_28d,
    round(median(hours_to_close) filter (
        where closed_at >= as_of_date - interval 28 day) / 24.0, 1) as median_days_to_close_28d,

    count(*) filter (where state = 'OPEN' and is_hard_blocker) as open_hard_blockers,
    count(*) filter (where state = 'OPEN' and is_customer_reported) as open_customer_reported
from i
