with source as (
    select * from {{ raw_source('issues__comments') }}
),

renamed as (
    select
        _dlt_id as comment_dlt_id,
        _dlt_parent_id as issue_dlt_id,
        _dlt_list_idx as comment_index,
        id as comment_id,
        url as comment_url,
        body,
        author__login as author_login,
        author__avatar_url as author_avatar_url,
        author_association,
        reactions_total_count,
        created_at
    from source
)

select * from renamed
