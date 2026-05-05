{# Single-row counts of open non-EPIC issues across the triage taxonomy. #}

with issue_triage as (
    select
        i.issue_dlt_id,
        i.state,
        i.issue_category,
        i.updated_at,
        max(case when l.label_name = 'triage' then 1 else 0 end) as has_triage,
        max(case when l.label_name = 'needs-repro' then 1 else 0 end) as has_needs_repro,
        max(case when l.label_name in ('has-repro', 'repro/verified') then 1 else 0 end) as has_repro_verified,
        max(case when l.label_name = 'hard-blocker' then 1 else 0 end) as has_hard_blocker,
        max(case when l.label_name = 'release/awaiting-release' then 1 else 0 end) as has_awaiting_release,
        max(case when l.label_name = 'cleanup/stale' then 1 else 0 end) as has_stale_label
    from {{ ref('fct_issues') }} i
    left join {{ ref('stg_issue_labels') }} l using (issue_dlt_id)
    where i.state = 'OPEN' and i.issue_category != 'epic'
    group by 1, 2, 3, 4
),

classified as (
    select
        *,
        case
            when has_awaiting_release = 1 then 'awaiting_release'
            when has_repro_verified = 1 then 'repro_verified'
            when has_needs_repro = 1 then 'needs_repro'
            when has_triage = 1 then 'triage_queue'
            else 'no_signal'
        end as triage_state,
        case
            when has_stale_label = 1 then 1
            when updated_at < current_date - interval '90 days' then 1
            else 0
        end as is_stale
    from issue_triage
)

select
    count(*) as total_open,
    count(case when triage_state = 'no_signal' then 1 end) as slipped_through_count,
    count(case when triage_state = 'triage_queue' then 1 end) as triage_queue_count,
    count(case when triage_state = 'needs_repro' then 1 end) as needs_repro_count,
    count(case when triage_state = 'repro_verified' then 1 end) as repro_verified_count,
    count(case when triage_state = 'awaiting_release' then 1 end) as awaiting_release_count,
    count(case when has_hard_blocker = 1 then 1 end) as hard_blocker_count,
    count(case when is_stale = 1 then 1 end) as stale_count,
    count(case when triage_state = 'no_signal' and issue_category = 'bug' then 1 end) as slipped_through_bugs,
    count(case when has_hard_blocker = 1 and has_awaiting_release = 0 then 1 end) as hard_blocker_unreleased
from classified
