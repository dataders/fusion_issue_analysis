with pull_requests as (
    select * from {{ ref('stg_pull_requests') }}
)

select
    pr_dlt_id,
    pr_number,
    pr_url,
    title,
    body,
    state,
    closed,
    author_login,
    author_association,
    reactions_total_count,
    comments_total_count,
    created_at,
    updated_at,
    closed_at,

    -- derived metrics
    case
        when state = 'MERGED' then true
        else false
    end as is_merged,

    case
        when closed_at is not null
        then date_diff('hour', created_at, closed_at)
    end as hours_to_close,

    case
        when state = 'MERGED' and closed_at is not null
        then date_diff('hour', created_at, closed_at)
    end as hours_to_merge

from pull_requests
