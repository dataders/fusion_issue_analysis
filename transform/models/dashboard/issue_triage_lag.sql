{#
  Rolling 7-day medians for triage SLAs.

  The raw GraphQL extract captures only the current label set, not label
  timeline events, so we approximate transition timestamps:
    - "first triage" ≈ first non-author comment (hours_to_first_response).
      A maintainer's first reply is the de-facto triage moment.
    - "triage → repro_verified" is approximated for bugs that currently carry
      the has-repro / repro/verified label, using updated_at - first_response_at
      as the elapsed verification time. This is a lower bound: updated_at
      shifts on any subsequent activity.
#}

with bugs as (
    select
        i.issue_dlt_id,
        i.created_at,
        i.first_response_at,
        i.updated_at,
        i.hours_to_first_response,
        max(case when l.label_name in ('has-repro', 'repro/verified') then 1 else 0 end) as has_repro_verified
    from {{ ref('fct_issues') }} i
    left join {{ ref('stg_issue_labels') }} l using (issue_dlt_id)
    where i.issue_category = 'bug'
    group by 1, 2, 3, 4, 5
),

triage_lag as (
    select median(hours_to_first_response) as median_hours_to_first_triage_bugs
    from bugs
    where created_at >= current_date - interval '7 days'
      and hours_to_first_response is not null
),

repro_lag as (
    select
        median(date_diff('hour', first_response_at, updated_at)) as median_hours_triage_to_repro_verified
    from bugs
    where has_repro_verified = 1
      and first_response_at is not null
      and updated_at >= current_date - interval '7 days'
)

select
    round(coalesce(triage_lag.median_hours_to_first_triage_bugs, 0) / 24.0, 1) as median_days_to_first_triage_bugs,
    round(coalesce(repro_lag.median_hours_triage_to_repro_verified, 0) / 24.0, 1) as median_days_triage_to_repro_verified,
    triage_lag.median_hours_to_first_triage_bugs as median_hours_to_first_triage_bugs,
    repro_lag.median_hours_triage_to_repro_verified as median_hours_triage_to_repro_verified
from triage_lag cross join repro_lag
