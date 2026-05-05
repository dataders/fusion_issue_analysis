{# Triage-lag metrics derived from real LABELED_EVENT timestamps.
   Replaces earlier comment-proxy approximations that used
   first non-author comment / updated_at as stand-ins. #}

with issues as (
    select
        issue_dlt_id,
        issue_number,
        issue_url,
        title,
        state,
        author_login,
        created_at as issue_created_at,
        closed_at
    from {{ ref('stg_issues') }}
),

label_events as (
    select
        issue_dlt_id,
        label_name,
        event_at
    from {{ ref('stg_issue_label_events') }}
    where event_type = 'LabeledEvent'
),

first_triage_event as (
    -- Earliest application of any label that signals an issue has entered
    -- the triage queue or been categorised as a bug.
    select
        issue_dlt_id,
        min(event_at) as first_triage_at
    from label_events
    where label_name in ('triage', 'needs-repro', 'bug')
    group by issue_dlt_id
),

first_repro_event as (
    -- Earliest application of any label that signals the bug has been
    -- reproduced/verified by a maintainer.
    select
        issue_dlt_id,
        min(event_at) as first_repro_at
    from label_events
    where label_name in ('repro/verified', 'has-repro', 'has_repro')
    group by issue_dlt_id
)

select
    i.issue_dlt_id,
    i.issue_number,
    i.issue_url,
    i.title,
    i.state,
    i.author_login,
    i.issue_created_at,
    i.closed_at,
    ft.first_triage_at,
    fr.first_repro_at,

    case
        when ft.first_triage_at is not null
            then date_diff('hour', i.issue_created_at, ft.first_triage_at)
    end as hours_to_first_triage,

    case
        when ft.first_triage_at is not null and fr.first_repro_at is not null
            then date_diff('hour', ft.first_triage_at, fr.first_repro_at)
    end as hours_triage_to_repro,

    case
        when fr.first_repro_at is not null
            then date_diff('hour', i.issue_created_at, fr.first_repro_at)
    end as hours_to_first_repro

from issues i
left join first_triage_event ft on i.issue_dlt_id = ft.issue_dlt_id
left join first_repro_event fr on i.issue_dlt_id = fr.issue_dlt_id
