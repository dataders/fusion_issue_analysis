with source as (
    select * from {{ raw_source('issues__assignees__nodes') }}
),

renamed as (
    select
        _dlt_id as assignee_dlt_id,
        _dlt_parent_id as issue_dlt_id,
        login as assignee_login,
        avatar_url as assignee_avatar_url,
        url as assignee_url
    from source
)

select * from renamed
