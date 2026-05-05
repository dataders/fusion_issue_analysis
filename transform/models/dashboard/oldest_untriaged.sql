{# Oldest open non-EPIC issues with zero triage signal — the daily action queue. #}

with issue_labels_agg as (
    select
        issue_dlt_id,
        max(case when label_name in (
            'triage', 'needs-repro', 'has-repro', 'repro/verified',
            'hard-blocker', 'release/awaiting-release', 'cleanup/stale'
        ) then 1 else 0 end) as has_triage_signal
    from {{ ref('stg_issue_labels') }}
    group by 1
)

select
    i.issue_number,
    i.title,
    i.author_login,
    i.issue_category,
    i.reactions_total_count,
    i.comments_total_count,
    i.issue_url,
    date_diff('day', i.created_at, current_date) as age_days,
    date_diff('day', i.updated_at, current_date) as days_since_activity
from {{ ref('fct_issues') }} i
left join issue_labels_agg l using (issue_dlt_id)
where i.state = 'OPEN'
  and i.issue_category != 'epic'
  and coalesce(l.has_triage_signal, 0) = 0
order by i.created_at asc
limit 25
