{#
  One row per dbt Fusion (engine:v2) issue. Every classification the
  dashboards use is decided here, once:
    - issue_category: bug | feature | task | epic | other
      (GitHub's native Issue Type wins; normalized type labels are the fallback)
    - triage_status:  awaiting_triage | needs_repro | has_repro | awaiting_release | triaged
    - flags:          is_customer_reported, is_hard_blocker, has_epic_parent, ...
#}

with issues as (
    select * from {{ ref('stg_issues') }}
),

milestones as (
    select
        milestone_number,
        milestone_title,
        milestone_state,
        milestone_due_on,
        milestone_created_at,
        milestone_closed_at
    from {{ ref('stg_milestones') }}
),

first_comments as (
    select
        issue_dlt_id,
        min(created_at) as first_comment_at
    from {{ ref('stg_issue_comments') }}
    group by issue_dlt_id
),

first_non_author_comments as (
    select
        c.issue_dlt_id,
        min(c.created_at) as first_response_at
    from {{ ref('stg_issue_comments') }} c
    inner join issues i
        on c.issue_dlt_id = i.issue_dlt_id
    where c.author_login != i.author_login
    group by c.issue_dlt_id
),

issue_labels as (
    select
        issue_dlt_id,
        count(*) as label_count,
        max(case when label_dimension = 'type' and label_value = 'bug' then 1 else 0 end) as has_bug_label,
        max(case when label_dimension = 'type' and label_value = 'feature' then 1 else 0 end) as has_feature_label,
        max(case when label_dimension = 'type' and label_value = 'epic' then 1 else 0 end) as has_epic_label,
        max(case when label_dimension = 'status' and label_value = 'awaiting_triage' then 1 else 0 end) as has_triage_label,
        max(case when label_dimension = 'status' and label_value = 'needs_repro' then 1 else 0 end) as has_needs_repro_label,
        max(case when label_dimension = 'status' and label_value = 'has_repro' then 1 else 0 end) as has_repro_label,
        max(case when label_dimension = 'status' and label_value = 'awaiting_release' then 1 else 0 end) as has_awaiting_release_label,
        max(case when label_dimension = 'priority' and label_value = 'hard_blocker' then 1 else 0 end) as has_hard_blocker_label,
        max(case when label_dimension = 'source' and label_value = 'customer' then 1 else 0 end) as has_customer_label
    from {{ ref('stg_issue_labels') }}
    group by issue_dlt_id
),

-- First time a maintainer removed the triage label = the issue was triaged.
triage_events as (
    select
        issue_dlt_id,
        min(event_at) as triaged_at
    from {{ ref('stg_issue_label_events') }}
    where event_type = 'UnlabeledEvent'
      and label_dimension = 'status'
      and label_value = 'awaiting_triage'
    group by issue_dlt_id
),

assignees as (
    select
        issue_dlt_id,
        count(*) as assignee_count
    from {{ ref('stg_issue_assignees') }}
    group by issue_dlt_id
),

classified as (
    select
        i.*,
        case
            when i.github_issue_type = 'Epic' or il.has_epic_label = 1 then 'epic'
            when i.github_issue_type = 'Bug' then 'bug'
            when i.github_issue_type in ('Feature', 'Enhancement') then 'feature'
            when i.github_issue_type = 'Task' then 'task'
            when il.has_bug_label = 1 then 'bug'
            when il.has_feature_label = 1 then 'feature'
            else 'other'
        end as issue_category,
        case
            when il.has_awaiting_release_label = 1 then 'awaiting_release'
            when il.has_repro_label = 1 then 'has_repro'
            when il.has_needs_repro_label = 1 then 'needs_repro'
            when il.has_triage_label = 1 then 'awaiting_triage'
            else 'triaged'
        end as triage_status,
        coalesce(il.label_count, 0) as label_count,
        coalesce(il.has_hard_blocker_label, 0) = 1 as is_hard_blocker,
        coalesce(il.has_customer_label, 0) = 1 as is_customer_reported,
        te.triaged_at,
        fc.first_comment_at,
        fnac.first_response_at,
        coalesce(a.assignee_count, 0) as assignee_count
    from issues i
    left join issue_labels il on i.issue_dlt_id = il.issue_dlt_id
    left join triage_events te on i.issue_dlt_id = te.issue_dlt_id
    left join first_comments fc on i.issue_dlt_id = fc.issue_dlt_id
    left join first_non_author_comments fnac on i.issue_dlt_id = fnac.issue_dlt_id
    left join assignees a on i.issue_dlt_id = a.issue_dlt_id
)

select
    c.issue_dlt_id,
    c.issue_number,
    c.issue_url,
    c.title,
    c.body,
    c.state,
    c.state_reason,
    c.closed,
    c.author_login,
    c.author_association,
    c.github_issue_type,
    c.issue_category,
    c.triage_status,
    c.milestone_number,
    m.milestone_title,
    m.milestone_state,
    m.milestone_due_on,
    m.milestone_created_at,
    m.milestone_closed_at,
    c.parent_number,
    c.parent_title,
    c.parent_issue_type,
    c.reactions_total_count,
    c.comments_total_count,
    c.created_at,
    c.updated_at,
    c.closed_at,
    c.triaged_at,
    c.first_comment_at,
    c.first_response_at,

    -- durations
    case when c.closed_at is not null then date_diff('hour', c.created_at, c.closed_at) end as hours_to_close,
    case when c.first_comment_at is not null then date_diff('hour', c.created_at, c.first_comment_at) end as hours_to_first_comment,
    case when c.first_response_at is not null then date_diff('hour', c.created_at, c.first_response_at) end as hours_to_first_response,
    case when c.triaged_at is not null then date_diff('hour', c.created_at, c.triaged_at) end as hours_to_triage,

    -- flags
    c.label_count,
    c.assignee_count,
    c.label_count > 0 as is_labeled,
    c.assignee_count > 0 as is_assigned,
    c.milestone_number is not null as has_milestone,
    c.is_hard_blocker,
    c.is_customer_reported,
    c.issue_category = 'epic' as is_epic,
    coalesce(c.parent_issue_type = 'Epic', false) as has_epic_parent,
    c.state = 'OPEN'
        and c.issue_category != 'epic'
        and not coalesce(c.parent_issue_type = 'Epic', false) as is_orphan

from classified c
left join milestones m
    on c.milestone_number = m.milestone_number
