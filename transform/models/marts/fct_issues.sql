with issues as (
    select * from {{ ref('stg_issues') }}
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
    inner join {{ ref('stg_issues') }} i
        on c.issue_dlt_id = i.issue_dlt_id
    where c.author_login != i.author_login
    group by c.issue_dlt_id
),

issue_labels as (
    select
        issue_dlt_id,
        max(case when label_name = 'bug' then 1 else 0 end) as has_bug,
        max(case when label_name = 'enhancement' then 1 else 0 end) as has_enhancement,
        max(case when label_name = 'EPIC' then 1 else 0 end) as has_epic,
        count(*) as label_count
    from {{ ref('stg_issue_labels') }}
    group by issue_dlt_id
),

triage_info as (
    select
        issue_dlt_id,
        count(*) as assignee_count
    from {{ ref('stg_issue_assignees') }}
    group by issue_dlt_id
)

select
    i.issue_dlt_id,
    i.issue_number,
    i.issue_url,
    i.title,
    i.body,
    i.state,
    i.closed,
    i.author_login,
    i.author_association,
    i.milestone_number,
    i.milestone_title,
    i.reactions_total_count,
    i.comments_total_count,
    i.created_at,
    i.updated_at,
    i.closed_at,

    -- derived metrics
    case
        when i.closed_at is not null
        then date_diff('hour', i.created_at, i.closed_at)
    end as hours_to_close,

    case
        when fc.first_comment_at is not null
        then date_diff('hour', i.created_at, fc.first_comment_at)
    end as hours_to_first_comment,

    case
        when fnac.first_response_at is not null
        then date_diff('hour', i.created_at, fnac.first_response_at)
    end as hours_to_first_response,

    fc.first_comment_at,
    fnac.first_response_at,

    -- classification
    case
        when il.has_epic = 1 then 'epic'
        when il.has_bug = 1 then 'bug'
        when il.has_enhancement = 1 then 'enhancement'
        else 'other'
    end as issue_category,

    -- triage fields
    coalesce(il.label_count, 0) as label_count,
    coalesce(ti.assignee_count, 0) as assignee_count,
    il.has_bug,
    il.has_enhancement,
    il.has_epic,
    case when coalesce(il.label_count, 0) > 0 then true else false end as is_labeled,
    case when coalesce(ti.assignee_count, 0) > 0 then true else false end as is_assigned,
    case when i.milestone_number is not null then true else false end as has_milestone

from issues i
left join first_comments fc
    on i.issue_dlt_id = fc.issue_dlt_id
left join first_non_author_comments fnac
    on i.issue_dlt_id = fnac.issue_dlt_id
left join issue_labels il
    on i.issue_dlt_id = il.issue_dlt_id
left join triage_info ti
    on i.issue_dlt_id = ti.issue_dlt_id
