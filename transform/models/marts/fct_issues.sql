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
    fnac.first_response_at

from issues i
left join first_comments fc
    on i.issue_dlt_id = fc.issue_dlt_id
left join first_non_author_comments fnac
    on i.issue_dlt_id = fnac.issue_dlt_id
